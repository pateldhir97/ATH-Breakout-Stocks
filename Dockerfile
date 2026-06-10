# Use the official AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.13

# Copy requirements and install dependencies into the Lambda task root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Lambda function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"]
