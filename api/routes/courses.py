"""
Course-related endpoints.

Provides access to course information via the Moodle adapter.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from plugins.coursepilot_webui_plugin.api.dependencies import MoodleDep
from utils.logger_util import Logger

router = APIRouter()
logger = Logger(name="CoursePilotAPI.courses")


class CourseResponse(BaseModel):
    """Response model for a course."""

    id: str
    name: str
    description: str | None = None


class CourseContentResponse(BaseModel):
    """Response model for course content."""

    course_id: str
    course_name: str
    sections: list[dict]


class ResourceResponse(BaseModel):
    """Response model for a resource."""

    id: str
    name: str
    type: str
    content: str | None = None


class SearchResultResponse(BaseModel):
    """Response model for search results."""

    query: str
    results: list[dict]
    total: int


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(adapter: MoodleDep):
    """
    List all available courses.

    Returns:
        List of courses the user has access to
    """
    try:
        # Using a default user_id for P0 - will be replaced with auth later
        courses = await adapter.get_courses(user_id="demo_user")
        return [
            CourseResponse(
                id=course.id,
                name=course.name,
                description=course.description,
            )
            for course in courses
        ]
    except Exception as e:
        logger.error(f"Error listing courses: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve courses")


@router.get("/courses/{course_id}", response_model=CourseContentResponse)
async def get_course(course_id: str, adapter: MoodleDep):
    """
    Get detailed content for a specific course.

    Args:
        course_id: The course identifier

    Returns:
        Course content including sections and resources
    """
    try:
        content = await adapter.get_course_content(course_id=course_id)
        return CourseContentResponse(
            course_id=content.course_id,
            course_name=content.course_name,
            sections=[section.model_dump() for section in content.sections],
        )
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Course {course_id} not found")


@router.get("/courses/{course_id}/resources/{resource_id}")
async def get_resource(course_id: str, resource_id: str, adapter: MoodleDep):
    """
    Get a specific resource from a course.

    Args:
        course_id: The course identifier
        resource_id: The resource identifier

    Returns:
        Resource metadata and content
    """
    try:
        resource = await adapter.get_resource(resource_id=resource_id)
        content = await adapter.get_resource_content(resource_id=resource_id)
        return ResourceResponse(
            id=resource.id,
            name=resource.name,
            type=resource.type,
            content=content,
        )
    except Exception as e:
        logger.error(f"Error getting resource {resource_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Resource {resource_id} not found")


@router.get("/courses/{course_id}/search", response_model=SearchResultResponse)
async def search_course(course_id: str, q: str, adapter: MoodleDep):
    """
    Search within a course's content.

    Args:
        course_id: The course identifier
        q: Search query

    Returns:
        Search results matching the query
    """
    try:
        results = await adapter.search(query=q, course_id=course_id)
        return SearchResultResponse(
            query=q,
            results=[r.model_dump() for r in results],
            total=len(results),
        )
    except Exception as e:
        logger.error(f"Error searching course {course_id}: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
