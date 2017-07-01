from zappa.async import run


def process_action(action_id):

    print "processing: %s" % action_id

    run(process_sub_task, (9,))

def process_sub_task(action_id):

    print "processing2: %s" % action_id