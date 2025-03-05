import json
import boto3
import librosa  # This is now available thanks to the layer!
import numpy as np  # No need to import explicitly, it's a librosa dependency
import io
import time

s3 = boto3.client('s3')
transcribe = boto3.client('transcribe')
comprehend = boto3.client('comprehend')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    try:
        # Get the bucket and key from the S3 event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        print(f"Processing file: s3://{bucket}/{key}")

        # Download the audio file from S3
        audio_file = s3.get_object(Bucket=bucket, Key=key)
        audio_bytes = audio_file['Body'].read()

        # 1. Transcribe the audio (using Amazon Transcribe)
        response = transcribe.start_transcription_job(
            TranscriptionJobName=key.replace('.', '_') + '_transcription',  # Unique job name
            LanguageCode='en-US',  # Change if your audio is in a different language
            MediaFormat='mp3',      # Adjust if your input file is not MP3
            Media={'MediaFileUri': f's3://{bucket}/{key}'},
            OutputBucketName=bucket # Save to same bucket.  Could make another.
        )
        # Wait for job to finish (with timeout)
        max_tries = 60  # Maximum wait time: 60 * 5 seconds = 5 minutes
        tries = 0
        while tries < max_tries:
            status = transcribe.get_transcription_job(TranscriptionJobName=response['TranscriptionJob']['TranscriptionJobName'])
            job_status = status['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                break
            print(f"Transcription Status: {job_status} (Attempt {tries+1}/{max_tries})")
            time.sleep(5)
            tries += 1

        if job_status != 'COMPLETED':
            raise Exception(f"Transcription job failed or timed out. Status: {job_status}")


        transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
        transcript_file_key = transcript_uri.split('/')[-1]
        transcript_file = s3.get_object(Bucket=bucket, Key=transcript_file_key)
        transcript_text = json.loads(transcript_file['Body'].read())['results']['transcripts'][0]['transcript']

        # 2. Extract audio features (using Librosa)
        y, sr = librosa.load(io.BytesIO(audio_bytes), sr=None)  # Load from bytes
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        chroma_stft = librosa.feature.chroma_stft(y=y, sr=sr)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)

        features = {
            'mfccs': mfccs.tolist(),  # Convert numpy arrays to lists for JSON
            'chroma_stft': chroma_stft.tolist(),
            'spectral_centroid': spectral_centroid.tolist(),
            'spectral_bandwidth': spectral_bandwidth.tolist(),
            'spectral_rolloff': spectral_rolloff.tolist()
        }

        # 3. Perform sentiment analysis (using Amazon Comprehend)
        # We perform sentiment analysis on the *Transcribed Text*
        comprehend_result = comprehend.detect_sentiment(Text=transcript_text, LanguageCode='en')
        sentiment = comprehend_result['Sentiment']
        sentiment_scores = comprehend_result['SentimentScore']


        # 4. Store the results in DynamoDB
        table = dynamodb.Table('AudioProcessingResults')  # Table name
        table.put_item(
            Item={
                'audio_file_key': key,
                'transcription': transcript_text,
                'features': features,
                'sentiment': sentiment,
                'sentiment_scores': sentiment_scores
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps('Audio processing complete!')
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error: {str(e)}")
        }