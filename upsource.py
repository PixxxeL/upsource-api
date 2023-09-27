import base64
import datetime
import json
import logging
import time

import requests


logger = logging.getLogger(__name__)


UPSOURCE_API = {
    'base_url' : 'https://upsource.example.com',
    'login' : 'user',
    'password' : 'secret',
}
API_BASE_URL = settings.UPSOURCE_API['base_url'] + '/~rpc'


class UpsourceApi:

    roles = {
        'Author': 1,
        'Reviewer': 2,
        'Watcher': 3,
    }

    participant_states = {
        'Unread': 1,
        'Read': 2,
        'Accepted': 3,
        'Rejected': 4,
    }

    def get_users(self):
        return self._get('findUsers', {
            'pattern': '',
            'limit': 100,
        }, 'infos')

    def get_projects(self):
        return self._get('getAllProjects', {
            'pattern': '',
            'limit': 100,
        }, 'project')

    def get_project_reviews(self, project_id, query=None, skip=0, limit=100):
        params = {
            'projectId': project_id,
            'skip': skip,
            'limit': limit,
        }
        if query:
            params['query'] = query
        return self._get('getReviews', params, 'reviews')

    def get_project_user_groups(self, project_id):
        return self._get('getProjectUserGroups', {
            'projectId': project_id,
            'limit': 100,
        }, 'groups')

    def get_revisions_list(self, project_id):
        return self._get('getRevisionsList', {
            'projectId': project_id,
            'limit': 100,
        }, 'revision')

    def get_review_details(self, project_id, review_id):
        return self._get('getReviewDetails', {
            'projectId': project_id,
            'reviewId': review_id,
        })

    def add_participant(self, review_dto, user_id, role):
        return self._get('addParticipantToReview', {
            'reviewId': review_dto,
            'participant': {
                'userId': user_id,
                'role': role,
            }
        })

    def add_group(self, review_dto, group_id, role=None):
        return self._get('addGroupToReview', {
            'reviewId': review_dto,
            'groupId': group_id,
            'role': role or self.roles['Reviewer'],
        })

    def remove_participant(self, review_dto, user_id, role=None):
        return self._get('removeParticipantFromReview', {
            'reviewId': review_dto,
            'participant': {
                'userId': user_id,
                'role': role or self.roles['Reviewer'],
            }
        })

    def add_deadline(self, review_dto, days=1):
        return self._get('setReviewDeadline', {
            'reviewId': review_dto,
            'deadline': future_timestamp_from_now(days=days),
        })

    def add_description(self, review_dto, text):
        return self._get('editReviewDescription', {
            'reviewId': review_dto,
            'text': text,
        })

    def update_reviewers_state(self, review_id, state, user_id):
        return self._get('updateReviewerState', {
            reviewId: review_id,
            state: state,
            userId: user_id,
        })

    def _get(self, meth, params, key=None, default=[]):
        url = f'{API_BASE_URL}/{meth}'
        params = self._get_params(data=params)
        response = requests.get(url, **params)
        logger.debug(f'Upsource API response {response.status_code} {response.text}')
        result = (json.loads(response.text) or {}).get('result', {})
        return result.get(key, default) if key else result

    def _get_params(self, data=None):
        key = '{login}:{password}'.format(**settings.UPSOURCE_API)
        key = base64.b64encode(key.encode('ascii')).decode('ascii')
        params = {
            'headers' : {
                'Authorization': f'Basic {key}',
            },
        }
        if data:
            params['params'] = {'params': json.dumps(data)}
        return params


def future_timestamp_from_now(days=1):
    now = datetime.datetime.now() # must make TZ
    deadline = now + datetime.timedelta(days=days)
    return int(time.mktime(deadline.timetuple()) * 1000)
