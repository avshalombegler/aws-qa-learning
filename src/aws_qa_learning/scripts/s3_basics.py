"""S3 basics demonstration - create bucket, upload, list, download, delete."""

from aws_qa_learning.aws_clients import create_s3_client

BUCKET_NAME = 's3-basics-demo'


def main() -> None:
    s3_client = create_s3_client()
    print('S3 client created.')

    s3_client.create_bucket(Bucket=BUCKET_NAME)
    print(f"Bucket '{BUCKET_NAME}' created.")

    objects_to_upload = [
        ('greetings/hello.txt', b'Hello, World!'),
        ('greetings/goodbye.txt', b'Bye, World!'),
    ]
    for key, body in objects_to_upload:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=body,
            ContentType='text/plain',
        )
    print(f'Uploaded {len(objects_to_upload)} objects.')

    response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix='greetings/')
    print(f"Objects in '{BUCKET_NAME}':")
    for obj in response.get('Contents', []):
        print(f'  - {obj["Key"]} ({obj["Size"]} bytes)')

    response = s3_client.get_object(Bucket=BUCKET_NAME, Key='greetings/hello.txt')
    content = response['Body'].read().decode('utf-8')
    print(f'Content of hello.txt: {content}')

    s3_client.delete_objects(
        Bucket=BUCKET_NAME,
        Delete={'Objects': [{'Key': key} for key, _ in objects_to_upload]},
    )
    print('Objects deleted.')

    s3_client.delete_bucket(Bucket=BUCKET_NAME)
    print(f"Bucket '{BUCKET_NAME}' deleted.")
    print('Done!')


if __name__ == '__main__':
    main()
