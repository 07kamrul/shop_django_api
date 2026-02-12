import random
from datetime import datetime, timedelta
from shop.models import EmailVerification, User


class VerificationService:
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))

    @staticmethod
    def create_verification(user, email):
        """Create email verification with OTP"""
        otp = VerificationService.generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)

        verification = EmailVerification.objects.create(
            user=user,
            email=email,
            otp=otp,
            expires_at=expires_at,
        )
        return verification

    @staticmethod
    def verify_otp(user_id, otp):
        """Verify OTP for user"""
        try:
            verification = EmailVerification.objects.filter(
                user_id=user_id,
                otp=otp,
                is_verified=False,
                expires_at__gt=datetime.now()
            ).latest('created_at')

            verification.is_verified = True
            verification.save(update_fields=["is_verified"])

            # Update user email verified status
            user = User.objects.get(pk=user_id)
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])

            return True
        except EmailVerification.DoesNotExist:
            return False

    @staticmethod
    def send_verification_email(email, otp):
        """Send OTP via email (placeholder for actual email service)"""
        # TODO: Implement actual email sending
        print(f"Sending OTP {otp} to {email}")
        return True
