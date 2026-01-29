from datetime import datetime

from .containers import Activity, BabyData, BreastfeedingActivity, DiaperActivity, DiaperTypes
from .exceptions import SnooBabyError
from .snoo import Snoo


class Baby:
    def __init__(self, baby_id: str, snoo: Snoo):
        self.baby_id = baby_id
        self.snoo = snoo
        self.baby_url = f"https://api-us-east-1-prod.happiestbaby.com/us/me/v10/babies/{self.baby_id}"
        self.activity_base_url = "https://api-us-east-1-prod.happiestbaby.com/cs/me/v11"

    @property
    def session(self):
        return self.snoo.session

    async def get_status(self) -> BabyData:
        hdrs = self.snoo.generate_snoo_auth_headers(self.snoo.tokens.aws_id)
        try:
            r = await self.session.get(self.baby_url, headers=hdrs)
            resp = await r.json()
        except Exception as ex:
            raise SnooBabyError from ex
        return BabyData.from_dict(resp)

    async def get_activity_data(self, from_date: datetime, to_date: datetime) -> list[Activity]:
        """Get activity data for this baby including feeding and diaper changes

        Args:
            from_date: Start date for activity range
            to_date: End date for activity range

        Returns:
            List of typed Activity objects (DiaperActivity or BreastfeedingActivity)
        """
        hdrs = self.snoo.generate_snoo_auth_headers(self.snoo.tokens.aws_id)

        url = f"{self.activity_base_url}/babies/{self.baby_id}/journals/grouped-tracking"

        params = {
            "group": "activity",
            "fromDateTime": from_date.astimezone().isoformat(timespec="milliseconds"),
            "toDateTime": to_date.astimezone().isoformat(timespec="milliseconds"),
        }

        try:
            r = await self.session.get(url, headers=hdrs, params=params)
            resp = await r.json()
            if r.status < 200 or r.status >= 300:
                raise SnooBabyError(f"Failed to get activity data: {r.status}: {resp}. Payload: {params}")

            activities: list[Activity] = []
            if isinstance(resp, list):
                for activity in resp:
                    activity_type = activity.get("type", "").lower()

                    if activity_type == "diaper":
                        activities.append(DiaperActivity.from_dict(activity))
                    elif activity_type == "breastfeeding":
                        activities.append(BreastfeedingActivity.from_dict(activity))
                    else:
                        # Other activity types exist but aren't supported yet
                        raise SnooBabyError(f"Unknown activity type: {activity_type}")
            else:
                raise SnooBabyError(f"Unexpected response format: {type(resp)}")

            return activities

        except Exception as ex:
            raise SnooBabyError from ex

    async def log_diaper_change(
        self,
        diaper_types: list[DiaperTypes],
        note: str | None = None,
        start_time: datetime | None = None,
    ) -> DiaperActivity:
        """Log a diaper change for this baby

        Args:
            diaper_types (list): List of diaper types. e.g. ['pee'], ['poo'], or ['pee', 'poo']
            note (str, optional): Optional note about the diaper change
            start_time (datetime, optional): Diaper change timestamp, doesn't allow length.
                Defaults to current local time if not provided.
        """

        if not start_time:
            start_time = datetime.now()

        # Always include the timezone indicator in the ISO string - seems to be required by the API
        if start_time.tzinfo is None:
            start_time = start_time.astimezone()

        hdrs = self.snoo.generate_snoo_auth_headers(self.snoo.tokens.aws_id)
        url = f"{self.activity_base_url}/journals"

        payload = {
            "babyId": self.baby_id,
            "data": {"types": [dt.value for dt in diaper_types]},
            "type": "diaper",
            "startTime": start_time.isoformat(timespec="milliseconds"),
        }

        if note:
            payload["note"] = note

        try:
            r = await self.session.post(url, headers=hdrs, json=payload)
            resp = await r.json()
            if r.status < 200 or r.status >= 300:
                raise SnooBabyError(f"Failed to log diaper change: {r.status}: {resp}. Payload: {payload}")
            return DiaperActivity.from_dict(resp)
        except Exception as ex:
            raise SnooBabyError from ex
