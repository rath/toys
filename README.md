# What's this #

toys

## notify ##

It publishs a message when a long job completed. 
If you build a large C++ project, you may 

	./configure && make | notify "Yay, Build completed!" 

Then, it will publish a message to the Topic ARN of your Amazon Simple Notification Service. 

