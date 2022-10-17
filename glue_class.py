import datetime
import io
import json
import logging
import os
import sys
import time
import uuid
import warnings
from typing import List, Tuple, Union

import boto3
import pandas as pd
from IPython.display import display
from sagemaker import get_execution_role

from glue_config import config_settings, template

warnings.filterwarnings("ignore")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("{0}.log".format(datetime.datetime.now().strftime("%Y-%m-%d"))),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('log')


class StartDocumentProcess:
    def __init__(self, list_of_jpg_: List[str], config_settings_: dict, template_: str):
        self.list_of_jpg = list_of_jpg_
        self.template = template_
        self.config_settings = config_settings_
        self.taskUIName = 'ui-textract-demo-' + now.strftime("%Y-%m-%d") + '0'
        self.humanTaskUiResponse = self.create_task_ui(self.taskUIName)
        self.humanTaskUiArn = self.humanTaskUiResponse['HumanTaskUiArn']
        self.count = 1

    def create_task_ui(self, task_ui_name: str):
        """
        Creates a Human Task UI resource.

        Returns:
        struct: HumanTaskUiArn
        """
        response = sagemaker.create_human_task_ui(
            HumanTaskUiName=task_ui_name,
            UiTemplate={'Content': self.template})
        return response

    def create_flow_definition(self, flow_definition_name: str):
        """
        Creates a Flow Definition resource

        Returns:
        struct: flow_definition_arn
        """
        humanloop_activation_conditions = json.dumps(config_settings)

        response = sagemaker.create_flow_definition(
            FlowDefinitionName=flow_definition_name,
            RoleArn=ROLE,
            HumanLoopConfig={
                "WorkteamArn": WORKTEAM_ARN,
                "HumanTaskUiArn": self.humanTaskUiArn,
                "TaskCount": 1,
                "TaskDescription": "Document analysis sample task description",
                "TaskTitle": "Document analysis sample task"
            },
            HumanLoopRequestSource={
                "AwsManagedHumanLoopRequestSource": "AWS/Textract/AnalyzeDocument/Forms/V1"
            },
            HumanLoopActivationConfig={
                "HumanLoopActivationConditionsConfig": {
                    "HumanLoopActivationConditions": humanloop_activation_conditions
                }
            },
            OutputConfig={
                "S3OutputPath": OUTPUT_PATH
            }
        )

        return response['FlowDefinitionArn']

    @staticmethod
    def analyze_document_with_a2i(document_name, hp_config):
        """
        Scan recognition.
        response -- recognited texts: dict
        """
        response = textract.analyze_document(
            Document={'S3Object': {'Bucket': BUCKET, 'Name': document_name}},
            FeatureTypes=["TABLES", "FORMS"],
            HumanLoopConfig=hp_config
        )
        return response

    def add_document_to_job(self,
                            nfhp: Union[List[str], None] = None,
                            results: Union[List[str], None] = None,
                            file_names: Union[List[str], None] = None) -> Tuple[List[List[str]],
                                                                                List[List[str]]]:
        """
        Download docs into HumanLoop.

        :param nfhp: сканы, не попавшие в джоб
        :param results: все распознанные сканы
        :param file_names: названия файлов
        :return: nfhp, file_names
        """
        if file_names is None:
            file_names = []
        if results is None:
            results = []
        if nfhp is None:
            nfhp = []
        hl = []  # scans' id
        flow_definition_name = now.strftime('%Y-%m-%d')
        flow_definition_arn = self.create_flow_definition(flow_definition_name)
        time.sleep(10)

        for element in self.list_of_jpg:
            time.sleep(2)
            name = element[0]
            logger.info('Document №{0} with name {1} is processing'.format(self.count, name))
            unique_id = str(uuid.uuid4())
            human_loop_unique_id = unique_id

            humanloop_config = {
                'FlowDefinitionArn': flow_definition_arn,
                'HumanLoopName': human_loop_unique_id,
                'DataAttributes': {'ContentClassifiers': ['FreeOfPersonallyIdentifiableInformation']}
            }
            analyze_document_response = self.analyze_document_with_a2i(name, humanloop_config)
            results.append(analyze_document_response)
            if 'HumanLoopArn' in analyze_document_response['HumanLoopActivationOutput']:
                logger.info('A human loop has been started with ARN: {0}'.format(
                    analyze_document_response["HumanLoopActivationOutput"]["HumanLoopArn"]))
                hl.append(analyze_document_response["HumanLoopActivationOutput"]["HumanLoopArn"].split('/')[-1])
                file_names.append([name, element[1]])
            else:
                nfhp.append([name, element[1]])
            self.count += 1
        self.doc_info(flow_definition_arn)

        return nfhp, file_names

    @staticmethod
    def doc_info(flow_definition_arn) -> None:
        time.sleep(10)
        all_human_loops_in_workflow = a2i_runtime_client.list_human_loops(FlowDefinitionArn=
                                                                          flow_definition_arn)['HumanLoopSummaries']

        # Check status of documents
        for human_loop in all_human_loops_in_workflow:
            logger.info('Human Loop Name: {0}'.format(human_loop["HumanLoopName"]))
            logger.info('Human Loop Status: {0}'.format(human_loop["HumanLoopStatus"]))

        workteam_name = WORKTEAM_ARN[WORKTEAM_ARN.rfind('/') + 1:]
        logger.info("Private worker portal adress: {0}".format(
            'https://' + sagemaker.describe_workteam(WorkteamName=workteam_name)['Workteam']['SubDomain']))


class MoveFileS3:
    def __init__(self, work_directory: str):
        self.work_directory = work_directory
        self.s3 = boto3.resource('s3')
        self.s3_client = boto3.client('s3')

    def upload_file_to_s3(self, path_to_csv: str, upload_s3_file: str, df_uploaded: pd.DataFrame) -> None:
        s3_path = self.work_directory + upload_s3_file
        df_uploaded.to_csv(path_to_csv, index=False)
        self.s3.meta.client.upload_file(path_to_csv, BUCKET, s3_path)

    def get_df_from_file_on_s3(self, path_to_csv: str, download_path: str) -> pd.DataFrame:
        key = self.work_directory + path_to_csv
        self.s3_client.download_file(BUCKET, key, download_path)
        df = pd.read_csv(download_path)
        return df


class PrepareDocuments:
    def __init__(self, list_of_names: List[str], path: List[str]):
        self.list_of_names = list_of_names
        self.path = path

    def converter_into_jpg(self) -> List[str]:
        pass

    def divide_doc_into_pages(self) -> List[str]:
        pass


class PostProcessing:
    def __init__(self, labels_: pd.DataFrame):
        self.labels = labels_

    def label_id_file(self, nfhp_: List[str], file_names_: List[str]) -> pd.DataFrame:

        post_labels = self.labels.set_index('id_')
        set_names = set(name.split('_')[0] + '.pdf' for name, _ in (file_names_ + nfhp_))

        # Updating file with labels
        all_names = self.labels['id_'].tolist()
        for _, name_ in enumerate(set_names):
            if name_ in all_names:
                post_labels.loc[name_, 'label'] = 'Yes'
        post_labels.reset_index(inplace=True)

        return post_labels



REGION = boto3.session.Session().region_name
BUCKET = "your-bucket-name"
OUTPUT_PATH = f's3://{BUCKET}/a2i-results-folder'
WORKTEAM_ARN = "arn:aws:sagemaker:***"
s3 = boto3.client('s3', REGION)
bucket_region = s3.head_bucket(Bucket=BUCKET)['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']
assert bucket_region == REGION, "Your S3 bucket {} and this notebook need to be in the same region.".format(BUCKET)
ROLE = get_execution_role()
display(ROLE)
dir_with_files = 'diff_files_folder/'
labels_path = 'labels_file.csv'

# Amazon SageMaker client
sagemaker = boto3.client('sagemaker', REGION)

# Amazon Textract client
textract = boto3.client('textract', REGION)

# S3 client
s3 = boto3.client('s3', REGION)

# A2I Runtime client
a2i_runtime_client = boto3.client('sagemaker-a2i-runtime', REGION)

now = datetime.datetime.now()

# Read csv from s3 bucket
download = MoveFileS3(dir_with_files)
labels = download.get_df_from_file_on_s3(labels_path, 'name.csv')

# Get list of jpg
list_of_docs = []
path_to_docs = []
preparation = PrepareDocuments(list_of_docs, path_to_docs)
# Needed actions to prepare documents

list_of_jpg = []  # received in the previous step
start = StartDocumentProcess(list_of_jpg, config_settings, template)
nfhp, file_names = start.add_document_to_job()


post_process = PostProcessing(labels)
labels = post_process.label_id_file(nfhp, file_names)
