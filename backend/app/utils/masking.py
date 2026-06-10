def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    if not local or not domain:
        return "***"
    return f"{local[0]}***@{domain}"


def mask_phone(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"


def mask_profile(profile: dict) -> dict:
    masked = dict(profile)
    if "email" in masked:
        masked["email"] = mask_email(str(masked["email"]))
    if "phone" in masked:
        masked["phone"] = mask_phone(str(masked["phone"]))
    return masked
