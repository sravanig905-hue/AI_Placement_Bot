def get_job_links(query):
    links = []

    query = query.lower()

    if "software" in query or "developer" in query:
        links.append("https://www.linkedin.com/jobs/software-engineer-jobs")
        links.append("https://www.naukri.com/software-developer-jobs")

    if "data" in query or "analyst" in query:
        links.append("https://www.linkedin.com/jobs/data-analyst-jobs")

    if "internship" in query:
        links.append("https://internshala.com/")

    if "ai" in query or "ml" in query:
        links.append("https://www.linkedin.com/jobs/machine-learning-jobs")

    return links