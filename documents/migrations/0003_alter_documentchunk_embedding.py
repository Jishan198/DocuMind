from django.db import migrations
from pgvector.django import VectorField


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_vector_index'),
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS documents_chunk_embedding_idx;",
            reverse_sql=""
        ),
        migrations.AlterField(
            model_name='documentchunk',
            name='embedding',
            field=VectorField(dimensions=3072),
        ),
    ]