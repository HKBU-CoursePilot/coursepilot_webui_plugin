"""
Course-related endpoints.

Provides access to course information via the Moodle adapter.

P0 Note: The IMoodlePort interface assumes course_id is always known
(user pre-selects course). For listing courses, we use hardcoded demo
data in P0. Real course listing will require API extension in P1.
"""

import os
import sys
from dataclasses import asdict

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.getcwd()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from plugins.coursepilot_webui_plugin.api.dependencies import MoodleDep
from plugins.moodle_adapter_plugin.exceptions import CourseNotFoundError, ItemNotFoundError
from utils.logger_util import Logger

router = APIRouter()
logger = Logger(name="CoursePilotAPI.courses")


# ============================================================================
# Response Models
# ============================================================================


class CourseResponse(BaseModel):
    """Response model for a course."""

    id: str
    code: str
    name: str
    instructor: str | None = None
    semester: str | None = None


class CourseContentResponse(BaseModel):
    """Response model for course content."""

    course_id: str
    sections: list[dict]


class ItemContentResponse(BaseModel):
    """Response model for item content."""

    item_id: str
    content: str


class SearchResultResponse(BaseModel):
    """Response model for search results."""

    query: str
    results: list[dict]
    total: int


# ============================================================================
# P0 Demo Data
# ============================================================================

# Hardcoded course list for P0 (real implementation needs get_courses() in IMoodlePort)
P0_DEMO_COURSES = [
    {"id": "demo_course", "code": "COMP1001", "name": "Introduction to Programming", 
     "instructor": "Dr. Demo", "semester": "2024-25 Sem 1"},
]


# ============================================================================
# Routes
# ============================================================================


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses():
    """
    List all available courses.

    P0: Returns hardcoded demo course list.
    P1: Will use IMoodlePort.get_courses() when implemented.

    Returns:
        List of courses the user has access to
    """
    # P0: Return hardcoded demo data
    # In P1+, this will call adapter.get_courses() once that method exists
    return [CourseResponse(**course) for course in P0_DEMO_COURSES]


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course_info(course_id: str, adapter: MoodleDep):
    """
    Get course metadata.

    Args:
        course_id: The course identifier

    Returns:
        Course information (code, name, instructor, semester)
    """
    try:
        info = await adapter.get_course_info(course_id=course_id)
        return CourseResponse(
            id=info.id,
            code=info.code,
            name=info.name,
            instructor=info.instructor,
            semester=info.semester,
        )
    except CourseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting course {course_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve course info")


@router.get("/courses/{course_id}/content", response_model=CourseContentResponse)
async def get_course_content(course_id: str, adapter: MoodleDep):
    """
    Get the full structured content of a course.

    Args:
        course_id: The course identifier

    Returns:
        Course content including all sections and items
    """
    try:
        content = await adapter.get_course_content(course_id=course_id)
        # Convert dataclass sections to dicts
        sections_data = []
        for section in content.sections:
            sections_data.append(asdict(section))
        
        return CourseContentResponse(
            course_id=content.course_id,
            sections=sections_data,
        )
    except CourseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting course content {course_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve course content")


@router.get("/courses/{course_id}/items/{item_id}", response_model=ItemContentResponse)
async def get_item_content(course_id: str, item_id: str, adapter: MoodleDep):
    """
    Get the extracted text content of a content item.

    Args:
        course_id: The course identifier (for URL structure, not used in lookup)
        item_id: The content item identifier

    Returns:
        Extracted text content of the item
    """
    try:
        content = await adapter.get_item_content(item_id=item_id)
        return ItemContentResponse(
            item_id=item_id,
            content=content,
        )
    except ItemNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting item {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve item content")


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
            results=[asdict(r) for r in results],
            total=len(results),
        )
    except CourseNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error searching course {course_id}: {e}")
        raise HTTPException(status_code=500, detail="Search failed")
