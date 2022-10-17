# AWS_Glue_TextractAnalyzeDocument
Запуск процесса обработки документов в AWS Glue с использованием встроенного сервиса ML Amazon Textract.

## Цель
Практически все статьи показывают, как запускать textract для обработки документов в Sagemaker. Однако в случае, если обработка должна быть запущена как постоянный процес (например, каждый день), jupiter notebook на большом количестве данных в Sagemaker периодически падает -> возникает необходимость перезапускать вручную.
Чтобы избежать необходимости постоянно чинить ноутбук, который не предназначен для такой задачи, можно запустить аналогичный процесс в сервисе ETL - AWS Glue.

## Запуск
Настройка среды для обработки документов в sagemaker здесь опускается. Описание детальной информации: https://docs.aws.amazon.com/sagemaker/latest/dg/a2i-textract-task-type.html

После того, как добавлены CORS policy и workteam arn, можно переходить к настройке job в Glue.
1. Создать job на основе Python Shell.

2. Job details: 
a. Меняем в параметре Data processing units 1/16 DPU -> 1 DPU (иначе может появиться ошибка памяти)
b. В пунке Job parameters добавляем Key: --additional-python-modules, Value: sagemaker,IPython.
При необходимости так же через запятую добавить дополнительные бибилиотеки.
c. Добавляем роль.

3. Создание IAM Role для Job'а.
Переходим в сервис Identity and Access Management -> Roles -> Create role -> Custom trust policy -> ...
В появившееся окно вставляем следующие настройки:
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "glue.amazonaws.com",
                    "sagemaker.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

... -> Next -> Add permissions -> ...
Добавляем следущие политики:
![photo_2022-10-18 00 13 57](https://user-images.githubusercontent.com/82960951/196284863-b24be9e9-0666-4b9e-8ba3-2fbf3b5d17dd.jpeg)

... -> Next -> Role name -> Create role.
