import boto3


def set_lex_permission_dev(event):

    set_lex_permission("handyfunapps", "parentorb", "devbot")

def set_lex_permission(profile, project, env):

    session = boto3.session.Session(profile_name="%s" % profile)
    client = session.client('lambda')
    client.add_permission(FunctionName="%s-%s" % (project, env),
                          Action="lambda:InvokeFunction",
                          Principal='lex.amazonaws.com',
                          StatementId="%s-%s_lex_invoke" % (project, env),
                          )