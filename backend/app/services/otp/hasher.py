import hashlib


class OtpHasher:

    @staticmethod
    def hash(
        otp: str,
    ) -> str:

        return hashlib.sha256(
            otp.encode()
        ).hexdigest()