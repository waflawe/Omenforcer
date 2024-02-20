from rest_framework.request import Request

from services.forum_mixins import AddInstanceMixin
from forum_app.models import Topic, Comments

from typing import Optional, Dict
import json


class AddInstanceAPIMixin(AddInstanceMixin):
    def add_instance(self, request: Request, is_instance_topic: Optional[bool] = True) -> Dict:
        topic_id = False if is_instance_topic else request.POST.get("topic", "")
        if not is_instance_topic:
            if not topic_id.isnumeric(): return {"success": "False", "errors": {"topic_id": {"code": "type"}}}
        instance = super().add_instance(request.user, request.POST, request.FILES, topic_id=topic_id)
        if isinstance(instance, (Topic, Comments)):
            return {"success": "True"}
        return {"success": "False", "errors": json.loads(instance.as_json())}
