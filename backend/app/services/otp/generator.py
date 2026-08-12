import secrets


class OtpGenerator:

    OTP_LENGTH = 6

    @classmethod
    def generate(cls) -> str:

        return (
            f"{secrets.randbelow(10**cls.OTP_LENGTH):0{cls.OTP_LENGTH}d}"
        )