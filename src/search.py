from src.services.job_service import JobService

service = JobService()


def search_jobs(keyword: str, location: str):
    return service.search(keyword, location)