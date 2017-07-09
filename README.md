# ParentOrb
A smart helper for parents with connected kids.

## Overview

- A chat bot using Amazon Lex.
- Stack is Python/Django/Postgres on Amazon Lambda
- Currently parents use a Facebook Messenger to interact with the bot. Kids use text messages.
- Zappa is used to deploy the bot to AWS/Lambda.
    - Two separate deployments are used (one for bot, and one foe website) but it is the same code base.

