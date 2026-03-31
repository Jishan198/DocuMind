from django.db import migrations





class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE INDEX IF NOT EXISTS documents_chunk_embedding_idx
                ON documents_chunk
                USING hnsw (embedding vector_cosine_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS documents_chunk_embedding_idx;"
        )
    ]