# ParentOrb
A smart helper for parents with connected kids. [Check out the website](http://parentorb.com/).

This was a side project I created to submit to the [AWS Chatbot Challange 2017](https://awschatbot2017.devpost.com/).

It didn't win, but it was a great opportunity to learn some new technology. 
I'm open sourcing because it's doing some cool things:
 - It's serverless! Not only the chatbot service, but the [django website](http://parentorb.com/), all in the same codebase. 
 - It works with [Facebook Messenger](https://m.me/2022397931327980).
 - A [router](bot/logic.py) and [tester](bot/parent_orb/tests) was made to easily create chat scripts and test them. 

## Overview

- A chat bot using Amazon Lex.
- Stack is Python/Django/Postgres on Amazon Lambda
- Currently parents use a Facebook Messenger to interact with the bot. Kids use text messages (via twilio).
- [Zappa](https://github.com/Miserlou/Zappa) is used to deploy the bot to AWS/Lambda.
    - Two separate deployments are used (one for bot, and one for website) but it is the same code base.
