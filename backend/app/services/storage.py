"""
File storage service using BackBlaze B2.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import BinaryIO, Tuple

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for uploading and managing files in BackBlaze B2."""

    def __init__(self):
        self.key_id = settings.B2_KEY_ID
        self.application_key = settings.B2_APPLICATION_KEY
        self.bucket_name = settings.B2_BUCKET_NAME
        self.auth_token = None
        self.api_url = None
        self.download_url = None

    async def _authenticate(self) -> None:
        """Authenticate with BackBlaze B2 API."""
        if not all([self.key_id, self.application_key]):
            raise ValueError("BackBlaze B2 credentials not configured")

        auth_url = "https://api.backblazeb2.com/b2api/v2/b2_authorize_account"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                auth_url, auth=(self.key_id, self.application_key)
            )
            response.raise_for_status()

            data = response.json()
            self.auth_token = data["authorizationToken"]
            self.api_url = data["apiUrl"]
            self.download_url = data["downloadUrl"]

        logger.info("Successfully authenticated with BackBlaze B2")

    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: str = "application/octet-stream",
    ) -> Tuple[str, str]:
        """
        Upload a file to BackBlaze B2.

        Args:
            file_content: Binary content of the file
            filename: Original filename
            content_type: MIME type of the file

        Returns:
            Tuple of (file_id, public_url)

        Raises:
            Exception: If upload fails
        """
        # Authenticate if needed
        if not self.auth_token:
            await self._authenticate()

        # Generate unique filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(file_content).hexdigest()[:8]
        unique_filename = f"{timestamp}_{file_hash}_{filename}"

        logger.info(f"Uploading file: {unique_filename}")

        # Get upload URL
        upload_url, upload_token = await self._get_upload_url()

        # Upload file
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Calculate SHA1 hash for integrity check
            sha1_hash = hashlib.sha1(file_content).hexdigest()

            response = await client.post(
                upload_url,
                headers={
                    "Authorization": upload_token,
                    "X-Bz-File-Name": unique_filename,
                    "Content-Type": content_type,
                    "X-Bz-Content-Sha1": sha1_hash,
                    "X-Bz-Info-src_filename": filename,
                },
                content=file_content,
            )
            response.raise_for_status()

            data = response.json()
            file_id = data["fileId"]

            # Generate public URL
            public_url = (
                f"{self.download_url}/file/{self.bucket_name}/{unique_filename}"
            )

            logger.info(f"File uploaded successfully: {file_id}")
            return file_id, public_url

    async def _get_upload_url(self) -> Tuple[str, str]:
        """
        Get upload URL and token from B2.

        Returns:
            Tuple of (upload_url, upload_token)
        """
        url = f"{self.api_url}/b2api/v2/b2_get_upload_url"

        # First, get bucket ID
        bucket_id = await self._get_bucket_id()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": self.auth_token},
                json={"bucketId": bucket_id},
            )
            response.raise_for_status()

            data = response.json()
            return data["uploadUrl"], data["authorizationToken"]

    async def _get_bucket_id(self) -> str:
        """
        Get bucket ID from bucket name.

        Returns:
            Bucket ID
        """
        url = f"{self.api_url}/b2api/v2/b2_list_buckets"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": self.auth_token},
                json={"accountId": self.key_id, "bucketName": self.bucket_name},
            )
            response.raise_for_status()

            data = response.json()
            buckets = data.get("buckets", [])

            if not buckets:
                raise ValueError(f"Bucket '{self.bucket_name}' not found")

            return buckets[0]["bucketId"]

    async def delete_file(self, file_id: str, filename: str) -> None:
        """
        Delete a file from BackBlaze B2.

        Args:
            file_id: The B2 file ID
            filename: The filename
        """
        if not self.auth_token:
            await self._authenticate()

        url = f"{self.api_url}/b2api/v2/b2_delete_file_version"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Authorization": self.auth_token},
                json={"fileId": file_id, "fileName": filename},
            )
            response.raise_for_status()

        logger.info(f"File deleted successfully: {file_id}")
