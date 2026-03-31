from rest_framework import serializers
from .models import Document


ALLOWED_EXTENSIONS = ['pdf', 'docx', 'txt']
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'file', 'file_type', 'file_size', 'status', 'created_at']
        read_only_fields = ['id', 'file_type', 'file_size', 'status', 'created_at']

    def validate_file(self, file):
        ext = file.name.split('.')[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        if file.size > MAX_FILE_SIZE:
            raise serializers.ValidationError("File too large. Maximum size is 20MB.")
        return file

    def create(self, validated_data):
        file = validated_data['file']
        ext = file.name.split('.')[-1].upper()
        validated_data['file_type'] = ext
        validated_data['file_size'] = file.size
        return super().create(validated_data)


class DocumentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file_type', 'file_size',
            'status', 'chunk_count', 'created_at'
        ]


class DocumentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file_type', 'file_size', 'status',
            'chunk_count', 'error_message', 'created_at', 'updated_at'
        ]