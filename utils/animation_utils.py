from enum import Enum
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QPoint, QRect, QParallelAnimationGroup, QSequentialAnimationGroup
from PyQt6.QtWidgets import QWidget, QGraphicsOpacityEffect, QGraphicsBlurEffect
from PyQt6.QtGui import QTransform
import random
import math


class AnimationType(Enum):
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    SLIDE_UP = "slide_up"
    SLIDE_DOWN = "slide_down"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    CROSS_FADE = "cross_fade"
    DISSOLVE = "dissolve"
    BLUR_FADE = "blur_fade"
    ROTATE_FADE = "rotate_fade"
    SLIDE_FADE = "slide_fade"
    BOUNCE_IN = "bounce_in"
    ELASTIC_IN = "elastic_in"


def create_fade_animation(widget: QWidget, duration: int = 1000,
                         fade_in: bool = True) -> QPropertyAnimation:
    """Create a fade in/out animation"""
    opacity_effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(opacity_effect)
    
    animation = QPropertyAnimation(opacity_effect, b"opacity")
    animation.setDuration(duration)
    
    if fade_in:
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
    else:
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    return animation


def create_slide_animation(widget: QWidget, direction: str, 
                          distance: int, duration: int = 1000) -> QPropertyAnimation:
    """Create a slide animation"""
    animation = QPropertyAnimation(widget, b"pos")
    animation.setDuration(duration)
    
    start_pos = widget.pos()
    end_pos = QPoint(start_pos)
    
    if direction == "left":
        animation.setStartValue(QPoint(start_pos.x() + distance, start_pos.y()))
        animation.setEndValue(start_pos)
    elif direction == "right":
        animation.setStartValue(QPoint(start_pos.x() - distance, start_pos.y()))
        animation.setEndValue(start_pos)
    elif direction == "up":
        animation.setStartValue(QPoint(start_pos.x(), start_pos.y() + distance))
        animation.setEndValue(start_pos)
    elif direction == "down":
        animation.setStartValue(QPoint(start_pos.x(), start_pos.y() - distance))
        animation.setEndValue(start_pos)
        
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    return animation


def create_zoom_animation(widget: QWidget, zoom_in: bool = True,
                         duration: int = 1000) -> QPropertyAnimation:
    """Create a zoom animation"""
    animation = QPropertyAnimation(widget, b"geometry")
    animation.setDuration(duration)
    
    current_rect = widget.geometry()
    center = current_rect.center()
    
    if zoom_in:
        # Start small, end at normal size
        small_width = int(current_rect.width() * 0.8)
        small_height = int(current_rect.height() * 0.8)
        small_rect = QRect(
            center.x() - small_width // 2,
            center.y() - small_height // 2,
            small_width,
            small_height
        )
        animation.setStartValue(small_rect)
        animation.setEndValue(current_rect)
    else:
        # Start normal, end large
        large_width = int(current_rect.width() * 1.2)
        large_height = int(current_rect.height() * 1.2)
        large_rect = QRect(
            center.x() - large_width // 2,
            center.y() - large_height // 2,
            large_width,
            large_height
        )
        animation.setStartValue(current_rect)
        animation.setEndValue(large_rect)
        
    animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    return animation


def create_combined_animation(widget: QWidget, animation_type: AnimationType,
                            duration: int = 1500):
    """Create animations based on type"""
    if animation_type == AnimationType.FADE:
        return create_fade_animation(widget, duration, fade_in=True)
    elif animation_type == AnimationType.SLIDE_LEFT:
        return create_slide_animation(widget, "left", widget.width() // 2, duration)
    elif animation_type == AnimationType.SLIDE_RIGHT:
        return create_slide_animation(widget, "right", widget.width() // 2, duration)
    elif animation_type == AnimationType.SLIDE_UP:
        return create_slide_animation(widget, "up", widget.height() // 3, duration)
    elif animation_type == AnimationType.SLIDE_DOWN:
        return create_slide_animation(widget, "down", widget.height() // 3, duration)
    elif animation_type == AnimationType.ZOOM_IN:
        return create_zoom_animation(widget, zoom_in=True, duration=duration)
    elif animation_type == AnimationType.ZOOM_OUT:
        return create_zoom_animation(widget, zoom_in=False, duration=duration)
    elif animation_type == AnimationType.DISSOLVE:
        return create_dissolve_animation(widget, duration)
    elif animation_type == AnimationType.SLIDE_FADE:
        direction = random.choice(["left", "right", "up", "down"])
        distance = widget.width() // 3 if direction in ["left", "right"] else widget.height() // 4
        return create_slide_fade_animation(widget, direction, distance, duration)
    elif animation_type == AnimationType.BOUNCE_IN:
        return create_bounce_in_animation(widget, duration)
    else:
        return create_fade_animation(widget, duration, fade_in=True)


def create_slide_fade_animation(widget: QWidget, direction: str,
                               distance: int, duration: int = 1200) -> QParallelAnimationGroup:
    """Create a combined slide and fade animation"""
    group = QParallelAnimationGroup()
    
    # Fade animation
    opacity_effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(opacity_effect)
    fade = QPropertyAnimation(opacity_effect, b"opacity")
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    fade.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    # Slide animation
    slide = create_slide_animation(widget, direction, distance, duration)
    
    group.addAnimation(fade)
    group.addAnimation(slide)
    return group


def create_dissolve_animation(widget: QWidget, duration: int = 1500) -> QPropertyAnimation:
    """Create a dissolve effect with smooth easing"""
    opacity_effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(opacity_effect)
    
    animation = QPropertyAnimation(opacity_effect, b"opacity")
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.InOutSine)
    return animation


def create_bounce_in_animation(widget: QWidget, duration: int = 1200) -> QParallelAnimationGroup:
    """Create a bounce-in effect"""
    group = QParallelAnimationGroup()
    
    # Fade
    opacity_effect = QGraphicsOpacityEffect()
    widget.setGraphicsEffect(opacity_effect)
    fade = QPropertyAnimation(opacity_effect, b"opacity")
    fade.setDuration(duration)
    fade.setStartValue(0.0)
    fade.setEndValue(1.0)
    
    # Scale bounce
    geometry = QPropertyAnimation(widget, b"geometry")
    geometry.setDuration(duration)
    current_rect = widget.geometry()
    center = current_rect.center()
    
    # Start small
    small_width = int(current_rect.width() * 0.3)
    small_height = int(current_rect.height() * 0.3)
    small_rect = QRect(
        center.x() - small_width // 2,
        center.y() - small_height // 2,
        small_width,
        small_height
    )
    
    geometry.setStartValue(small_rect)
    geometry.setEndValue(current_rect)
    geometry.setEasingCurve(QEasingCurve.Type.OutElastic)
    
    group.addAnimation(fade)
    group.addAnimation(geometry)
    return group


def get_random_animation_type() -> AnimationType:
    """Get a random animation type"""
    # Weight certain animations more heavily for better visual experience
    weighted_choices = [
        AnimationType.FADE,
        AnimationType.FADE,
        AnimationType.DISSOLVE,
        AnimationType.DISSOLVE,
        AnimationType.SLIDE_FADE,
        AnimationType.SLIDE_LEFT,
        AnimationType.SLIDE_RIGHT,
        AnimationType.ZOOM_IN,
        AnimationType.BOUNCE_IN,
        AnimationType.SLIDE_UP,
    ]
    return random.choice(weighted_choices)