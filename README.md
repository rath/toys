# What's this #

toys

## notify ##

*notify* will publish a message to Amazon SNS after a long job has done. 

If you build a large C++ project, you may 

	./configure && make | notify "Yay, Build completed!" 

Then, it will publish a message to the Topic ARN for Amazon Simple Notification Service. 

You should set up your credentials (Access Key ID and Secret Access Key), host and Topic ARN to publish messages to Amazon SNS. 
Create a file named *.aws_access* on your home directory. 

	vi $HOME/.aws_access

then, 

	aws.id=YOUR_ACCESS_KEY_ID
	aws.secret=YOUR_SECRET_ACCESS_KEY
	aws.sns.host=sns.eu-west-1.amazonaws.com 
	aws.sns.topic=arn:aws:sns:eu-west-1:YOUR_ACCOUNT_NUMBER:build

You can override these credentials by setting environment variable named *AWS_ACCESS_ID*, *AWS_ACCESS_SECRET*, *AWS_SNS_HOST*, and *AWS_SNS_TOPIC*.
