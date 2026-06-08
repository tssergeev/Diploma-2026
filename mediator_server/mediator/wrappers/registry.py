from .base import BaseRestWrapper
from .fitness_app import FitnessAppWrapper
from .fitness_club import FitnessClubWrapper
from .sports_school import SportsSchoolWrapper


WRAPPER_BY_TYPE = {
    "fitness_club": FitnessClubWrapper,
    "sports_school": SportsSchoolWrapper,
    "fitness_app": FitnessAppWrapper,
    "generic_rest": BaseRestWrapper,
}


def get_wrapper(source):
    wrapper_class = WRAPPER_BY_TYPE.get(source.source_type, BaseRestWrapper)
    return wrapper_class(source)
