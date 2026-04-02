import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from documents.models import Document
from documents.services.chunker import DocumentChunker
from documents.services.extractor import TextExtractor


@pytest.mark.django_db
class TestDocumentUpload:
    def test_upload_requires_login(self, client):
        response = client.post(reverse('upload_document'))
        assert response.status_code == 302

    def test_viewer_cannot_upload(self, client, viewer_user, viewer_membership):
        client.force_login(viewer_user)
        pdf = SimpleUploadedFile('test.pdf', b'%PDF-1.4 fake content', content_type='application/pdf')
        response = client.post(reverse('upload_document'), {
            'title': 'Test',
            'file': pdf
        })
        assert b'Viewers cannot upload' in response.content

    def test_unsupported_file_type_rejected(self, auth_client):
        exe = SimpleUploadedFile('malware.exe', b'MZ fake exe', content_type='application/octet-stream')
        response = auth_client.post(reverse('upload_document'), {
            'title': 'Bad File',
            'file': exe
        })
        assert b'Unsupported file type' in response.content

    def test_oversized_file_rejected(self, auth_client):
        large_file = SimpleUploadedFile(
            'big.pdf',
            b'%PDF' + b'x' * (21 * 1024 * 1024),
            content_type='application/pdf'
        )
        response = auth_client.post(reverse('upload_document'), {
            'title': 'Big File',
            'file': large_file
        })
        assert b'too large' in response.content


class TestDocumentChunker:
    def test_chunker_splits_text(self):
        chunker = DocumentChunker(chunk_size=10, overlap=2)
        pages = [(1, 'word ' * 30)]
        chunks = chunker.chunk_pages(pages)
        assert len(chunks) > 1

    def test_chunker_preserves_page_number(self):
        chunker = DocumentChunker(chunk_size=10, overlap=2)
        pages = [(3, 'word ' * 15)]
        chunks = chunker.chunk_pages(pages)
        assert all(c.page_number == 3 for c in chunks)

    def test_chunker_overlap_creates_more_chunks(self):
        chunker_no_overlap = DocumentChunker(chunk_size=10, overlap=0)
        chunker_overlap = DocumentChunker(chunk_size=10, overlap=5)
        pages = [(1, 'word ' * 50)]
        chunks_no_overlap = chunker_no_overlap.chunk_pages(pages)
        chunks_overlap = chunker_overlap.chunk_pages(pages)
        assert len(chunks_overlap) > len(chunks_no_overlap)

    def test_empty_text_returns_no_chunks(self):
        chunker = DocumentChunker()
        chunks = chunker.chunk_pages([(1, '')])
        assert len(chunks) == 0


class TestTextExtractor:
    def test_txt_extraction(self, tmp_path):
        txt_file = tmp_path / 'test.txt'
        txt_file.write_text('Hello world from DocuMind.')
        extractor = TextExtractor()
        pages = extractor.extract(str(txt_file), 'TXT')
        assert len(pages) == 1
        assert 'Hello world' in pages[0][1]

    def test_unsupported_type_raises(self, tmp_path):
        f = tmp_path / 'file.xyz'
        f.write_text('data')
        extractor = TextExtractor()
        with pytest.raises(ValueError):
            extractor.extract(str(f), 'XYZ')
# Create your tests here.
