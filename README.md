# What's this #

toys

## notify ##

It publishs a message when a long job completed. 
If you build a large C++ project, you may 

	./configure && make | notify "Yay, Build completed!" 

Then, it will publish a message to the Topic ARN of your Amazon Simple Notification Service. 

You should change 2 variables before using *notify*. 
The first is *HOST* (notify:7), its default value is 'sns.eu-west-1.amazonaws.com' which is my base region. 
The second is *TOPIC_ARN* (notify:8), you easily pick this up on https://console.aws.amazon.com/sns/home 

Finally, you should set up Access Key ID and Secret Access Key to publish messages to Amazon SNS. 
Create a file named *.aws_access* on your home directory. 

	vi ~/.aws_access

then, 

	aws.id=YOUR_ACCESS_KEY_ID
	aws.secret=YOUR_SECRET_ACCESS_KEY

You can override these credentials by setting environment variable named *AWS_ACCESS_ID* and *AWS_ACCESS_SECRET*.
