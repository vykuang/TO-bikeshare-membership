# Working with AWS

## EC2

With `awscli` installed, this is handy to list all public IPs of our instances:

```bash
aws ec2 describe-instances \
  --filter "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[*].[PublicIpAddress, Tags[?Key=='Name'].Value|[0]]" \
  --output text
```

## S3

S3 is object store, and uses `key-value` pairs and buckets to identify and manage objects. No directory hierarchy, but can be built into the `key` value of object with slash `/`

* key - name of object
    * Should also include the subdir of the object in the bucket
* value - content, also referred to as `body`

### S3 Permissions

* s3:PutObject to store
* s3:ListBucket to retrieve, amongst others.

### Object interaction

* CLI:

```bash
# upload
aws s3api put-object --bucket text-content --key dir-1/my_images.tar.bz2 --body my_images.tar.bz2
# retrieve
aws s3api get-object --bucket text-content --key dir-1/my_images.tar.bz2 --body my_images.tar.bz2
```

* Python SDK

```py
import boto3
client = boto3.client('s3')

put_response = client.put_object(
    Body=b'bytes'|file,
    Bucket='string',
    Key='string',
)

get_response = client.get_object(
    Bucket='string',
    Key='string',
)
obj = get_response['Body']

# alternative, downloading to file
s3.meta.client.download_file(
    Bucket='mybucket', 
    Key='hello.txt', 
    Filename='/tmp/hello.txt')

```

## Credentials

For docker to access AWS resources, attach the local ~/.aws/credentials as volume.

However for docker running on EC2, they get the EC2 creds for free [See docs](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/iam-roles-for-amazon-ec2.html)

docker can also retrieve creds from the instance's private IP

Problem with passing .env is that `printenv` commands inside the container will expose the keys, but one could argue that if access to the containers is compromised then all is already lost.

### Profiles

`aws configure --profile <my_profile>` to set creds for specific profiles

* Pass profile to docker containers with `AWS_PROFILE` env var