from rest_framework import serializers
from .models import QueryLog


class QueryRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)


class SourceSerializer(serializers.Serializer):
    document_title = serializers.CharField()
    document_id = serializers.UUIDField()
    page_number = serializers.IntegerField()
    chunk_index = serializers.IntegerField()
    score = serializers.FloatField()


class QueryResponseSerializer(serializers.Serializer):
    question = serializers.CharField()
    answer = serializers.CharField()
    sources = SourceSerializer(many=True)
    tokens_used = serializers.IntegerField()
    response_time_ms = serializers.IntegerField()


class QueryLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = QueryLog
        fields = [
            'id', 'question', 'answer', 'sources',
            'tokens_used', 'response_time_ms', 'created_at'
        ]
        