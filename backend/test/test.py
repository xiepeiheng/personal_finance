import os
import django
import rest_framework
import io

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from datetime import datetime
from rest_framework import serializers
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer

class Comment:
    def __init__(self, email, content, created=None):
        self.email = email
        self.content = content
        self.created = created or datetime.now()

comment = Comment(email='leila@example.com', content='foo bar')

class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=200)
    created = serializers.DateTimeField()

serializer = CommentSerializer(comment)
print(serializer.data, type(serializer.data))
# {'email': 'leila@example.com', 'content': 'foo bar', 'created': '2026-04-21T10:46:19.932346+08:00'} <class 'rest_framework.utils.serializer_helpers.ReturnDict'>
json = JSONRenderer().render(serializer.data)
print(json, type(json))
# {'email': 'leila@example.com', 'content': 'foo bar', 'created': '2026-04-21T10:38:26.172047+08:00'}


stream = io.BytesIO(json)
data = JSONParser().parse(stream)
print(data, type(data))
serializer = CommentSerializer(data=data)
print(serializer.is_valid())
# True
print(serializer.validated_data, type(json))
# {'email': 'leila@example.com', 'content': 'foo bar', 'created': datetime.datetime(2026, 4, 21, 10, 46, 19, 932346, tzinfo=zoneinfo.ZoneInfo(key='Asia/Shanghai'))}