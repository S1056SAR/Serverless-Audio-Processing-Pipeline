# Serverless-Audio-Processing-Pipeline

This project implements a serverless audio processing pipeline on AWS that automatically transcribes audio files, extracts key audio features, and performs sentiment analysis on the transcribed text. It's designed to be scalable, cost-effective, and fully managed by AWS services.

## Overview

The pipeline is triggered when an MP3 audio file is uploaded to a designated Amazon S3 bucket.  Upon upload, an AWS Lambda function is invoked. This function performs the following steps:

1.  **Transcription:**  Uses Amazon Transcribe to convert the audio to text. The transcription is saved back into same S3 Bucket.
2.  **Feature Extraction:**  Uses the Librosa library (included as a Lambda Layer) to extract audio features such as MFCCs, chroma, spectral centroid, spectral bandwidth, and spectral rolloff.
3.  **Sentiment Analysis:** Uses Amazon Comprehend to analyze the sentiment of the *transcribed text*.
4.  **Data Storage:**  Stores the transcription, extracted features, and sentiment analysis results in an Amazon DynamoDB table.

## Architecture
content_copy
download
Use code with caution.
Markdown

[MP3 Audio File] --> [S3 Bucket] --(ObjectCreated Event)--> [Lambda Function]
|
+--> [Amazon Transcribe] --> [Transcription]
|
+--> [Librosa] --> [Audio Features]
|
+--> [Amazon Comprehend] --> [Sentiment]
|
+--> [DynamoDB] (Store Results)

## Technologies Used

*   **Languages:** Python 3.9, YAML
*   **Frameworks/Libraries:** Librosa, NumPy, SciPy, boto3
*   **Databases:** Amazon DynamoDB
*   **Tools:** Git, Docker, AWS CLI, AWS Toolkit for VS Code, VS Code
*   **Cloud:** AWS (S3, Lambda, DynamoDB, Transcribe, Comprehend, IAM, CloudFormation/SAM, CloudWatch)

## Prerequisites

*   An active AWS account with appropriate IAM permissions (to create S3 buckets, Lambda functions, DynamoDB tables, IAM roles, etc.).
*   AWS CLI installed and configured with your credentials.
*   Docker installed (for building the Librosa Lambda Layer).
*   Python 3.8 or later installed locally.
*   VS Code (recommended) with the AWS Toolkit extension.

## Setup and Deployment

These instructions assume you are using VS Code with the AWS Toolkit.  You can adapt them for the AWS CLI if needed.

1.  **Clone the Repository (If Applicable):**
    ```bash
    git clone <repository_url>
    cd serverless-audio-pipeline
    ```

2.  **Create the Librosa Lambda Layer:**
    *   Navigate to the `librosa_layer` directory:

        ```bash
        cd librosa_layer
        ```
    *   Create `requirements.txt` with content `librosa`
    *    Create the `python` directory
        ```bash
        mkdir -p python
        ```
    *   Build the layer using Docker:

        ```bash
        docker run -v "${PWD}":/var/task "public.ecr.aws/sam/build-python3.9" /bin/sh -c "pip install -r requirements.txt -t python/; exit"
        zip -r ../librosa_layer.zip .
        ```
        ```bash
        cd ..
        ```

3.  **Create an S3 Bucket:**

    *   Use the AWS Toolkit in VS Code (recommended) or the AWS CLI to create a *globally unique* S3 bucket.  Note the bucket name – you'll need it later.
     *   Example (using a dynamic name in the CloudFormation template): `your-unique-bucket-name-ACCOUNT_ID-REGION` (replace `your-unique-bucket-name`, `ACCOUNT_ID`, and `REGION` with appropriate values).

4. **Upload `librosa_layer.zip` to S3:**
      ```bash
        aws s3 cp librosa_layer.zip s3://your-unique-bucket-name-ACCOUNT_ID-REGION/
      ```

5.  **Deploy the CloudFormation Stack:**

    *   **Using AWS Toolkit (Recommended):**
        1.  In VS Code, open the AWS Toolkit view.
        2.  In the CloudFormation explorer, right-click on the `infrastructure/template.yaml` file.
        3.  Choose "Deploy Serverless Application...".
        4.  Follow the prompts:
            *   Create a new stack (or update an existing one).
            *   Give your stack a name (e.g., `audio-processing-stack`).
            *   Select the S3 bucket you created.
            *   Confirm the region.
            *   Acknowledge IAM capabilities.
        5. Click "Deploy"

    *   **Using AWS CLI (Alternative):**

        ```bash
        cd serverless-audio-pipeline #Ensure to be one level up
        aws cloudformation package \
          --template-file infrastructure/template.yaml \
          --s3-bucket your-unique-bucket-name-ACCOUNT_ID-REGION \
          --output-template-file packaged-template.yaml

        aws cloudformation deploy \
          --template-file packaged-template.yaml \
          --stack-name audio-processing-stack \
          --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
          --region your-aws-region
        ```

6. **Project Structure:**

    ```
    serverless-audio-pipeline/
    ├── lambda_function/
    │   ├── lambda_function.py        # Main Lambda function code
    │   └── requirements.txt         # (Empty in this case, as Librosa is in the layer)
    ├── librosa_layer/              # Directory for the Librosa Lambda Layer
    │   └── python/                  # This structure is required by Lambda Layers
    │       └── (Librosa and dependencies will be placed here by Docker)
    ├── infrastructure/
    │   └── template.yaml          # CloudFormation template (infrastructure as code)
    └── README.md                 # Project documentation
    ```

## Testing

1.  Upload an MP3 audio file to your S3 bucket.
2.  Monitor the Lambda function's logs in CloudWatch (accessible through the AWS Toolkit in VS Code).
3.  Check your DynamoDB table (`AudioProcessingResults`) for the processed data (transcription, features, sentiment).

## Cleanup

To remove all deployed resources, delete the CloudFormation stack:

*   **Using AWS Toolkit:** Right-click on the stack in the CloudFormation explorer and choose "Delete Stack".
*   **Using AWS CLI:**

    ```bash
    aws cloudformation delete-stack --stack-name audio-processing-stack --region your-aws-region
    ```

## Troubleshooting
* Check the Cloudwatch logs in case of any error.

## Contributing

Contributions are welcome! Please submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (You should create a LICENSE file).
content_copy
download
Use code with caution.

Key improvements and explanations in this README:

Clear Overview: Provides a concise summary of the project's purpose and functionality.

Architecture Diagram: A simple text-based diagram helps visualize the data flow.

Technologies Used: A well-organized list of all technologies involved.

Prerequisites: Clearly states the required software and accounts.

Setup and Deployment: Detailed, step-by-step instructions, tailored for VS Code and the AWS Toolkit (with CLI alternatives). Includes all necessary commands.

Project Structure: Shows the directory layout, making it easy to understand the organization of the code.

Testing: Explains how to test the deployed pipeline.

Cleanup: Provides clear instructions on how to remove the deployed resources to avoid unnecessary costs.

Troubleshooting: Basic troubleshooting

Contributing: Encourages contributions (optional).

License: Includes a placeholder for a license file (you should create a LICENSE file and choose an appropriate open-source license, like MIT).

Markdown Formatting: Uses Markdown for readability and structure.

Docker Instructions: Ensures that Docker instructions are clear and accurate.

Cloudformation Instructions: Provides both AWS Toolkit and CLI instructions.

S3 Bucket: Uses a combination of a user-provided prefix and AWS account/region for the S3 bucket name to prevent naming conflicts.

Error Handling and Robustness: Adds basic error handling to the Lambda and improves the instructions.

This comprehensive README will make it much easier for others (and your future self!) to understand, use, and contribute to your project. It also demonstrates good software engineering practices.
