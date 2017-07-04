from django.core.exceptions import ObjectDoesNotExist

from core.models import Action, AppUser
from zappa.async import run
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def process_all_actions():
    actions = Action.get_actions_to_process()
    logger.info("found %s actions to process" % actions.count())

    for a in actions:
        run(process_action, (a.id,))


def process_action(action_id):

    try:
        action = Action.objects.get(id=action_id)
    except ObjectDoesNotExist:
        logger.error("action_id not found: %s", action_id)
        return

    logger.info("processing: %s", action.id)
    action.process()


def schedule_all_users():

    users = AppUser.get_users_to_schedule()
    logger.info("found %s users to schedule" % users.count())

    for u in users:
        run(schedule_user, (u.id,))


def schedule_user(user_id):

    try:
        user = AppUser.objects.get(id=user_id)
    except ObjectDoesNotExist:
        logger.error("user_id not found: %s", user_id)
        return

    logger.info("scheduling: %s", user.id)
    user.schedule_actions()



