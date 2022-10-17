# examples

template = r"""
<script src="https://assets.crowd.aws/crowd-html-elements.js"></script>
{% capture s3_arn %}http://s3.amazonaws.com/{{ task.input.aiServiceRequest.document.s3Object.bucket }}/{{ task.input.aiServiceRequest.document.s3Object.name }}{% endcapture %}
<crowd-form>
  <crowd-textract-analyze-document 
      src="{{ s3_arn | grant_read_access }}" 
      initial-value="{{ task.input.selectedAiServiceResponse.blocks }}" 
      header="Review the key-value pairs listed on the right and correct them if they don't match the following document." 
      no-key-edit="" 
      no-geometry-edit="" 
      keys="{{ task.input.humanLoopContext.importantFormKeys }}" 
      block-types="['KEY_VALUE_SET']">
    <short-instructions header="Instructions">
        <p>Click on a key-value block to highlight the corresponding key-value pair in the document.
        </p><p><br></p>
        <p>If it is a valid key-value pair, review the content for the value. If the content is incorrect, correct it.
        </p><p><br></p>
        <p>The text of the value is incorrect, correct it.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/correct-value-text.png">
        </p><p><br></p>
        <p>A wrong value is identified, correct it.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/correct-value.png">
        </p><p><br></p>
        <p>If it is not a valid key-value relationship, choose No.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/not-a-key-value-pair.png">
        </p><p><br></p>
        <p>If you can’t find the key in the document, choose Key not found.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/key-is-not-found.png">
        </p><p><br></p>
        <p>If the content of a field is empty, choose Value is blank.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/value-is-blank.png">
        </p><p><br></p>
        <p><strong>Examples</strong></p>
        <p>Key and value are often displayed next or below to each other.
        </p><p><br></p>
        <p>Key and value displayed in one line.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/sample-key-value-pair-1.png">
        </p><p><br></p>
        <p>Key and value displayed in two lines.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/sample-key-value-pair-2.png">
        </p><p><br></p>
        <p>If the content of the value has multiple lines, enter all the text without line break. 
        Include all value text even if it extends beyond the highlight box.</p>
        <p><img src="https://assets.crowd.aws/images/a2i-console/multiple-lines.png"></p>
    </short-instructions>
    <full-instructions header="Instructions"></full-instructions>
  </crowd-textract-analyze-document>
</crowd-form>
"""

config_settings = {
    "Conditions": [
        {
            "Or": [

                {
                    "ConditionType": "ImportantFormKeyConfidenceCheck",
                    "ConditionParameters": {
                        "ImportantFormKey": "Mail address",
                        "ImportantFormKeyAliases": ["Mail Address:", "Mail address:", "Mailing Add:",
                                                    "Mailing Addresses"],
                        "KeyValueBlockConfidenceLessThan": 100,
                        "WordBlockConfidenceLessThan": 100
                    }
                },
                {
                    "ConditionType": "MissingImportantFormKey",
                    "ConditionParameters": {
                        "ImportantFormKey": "Mail address",
                        "ImportantFormKeyAliases": ["Mail Address:", "Mail address:", "Mailing Add:",
                                                    "Mailing Addresses"]
                    }
                },
                {
                    "ConditionType": "ImportantFormKeyConfidenceCheck",
                    "ConditionParameters": {
                        "ImportantFormKey": "Phone Number",
                        "ImportantFormKeyAliases": ["Phone number:", "Phone No.:", "Number:"],
                        "KeyValueBlockConfidenceLessThan": 100,
                        "WordBlockConfidenceLessThan": 100
                    }
                },
                {
                    "ConditionType": "ImportantFormKeyConfidenceCheck",
                    "ConditionParameters": {
                        "ImportantFormKey": "*",
                        "KeyValueBlockConfidenceLessThan": 100,
                        "WordBlockConfidenceLessThan": 100
                    }
                },
                {
                    "ConditionType": "ImportantFormKeyConfidenceCheck",
                    "ConditionParameters": {
                        "ImportantFormKey": "*",
                        "KeyValueBlockConfidenceGreaterThan": 0,
                        "WordBlockConfidenceGreaterThan": 0
                    }
                }
            ]
        }
    ]
}
