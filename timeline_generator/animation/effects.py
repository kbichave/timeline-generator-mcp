"""Animation transition effects."""

from abc import ABC, abstractmethod
from enum import Enum
import math


class EasingFunction(str, Enum):
    """Available easing functions."""
    
    LINEAR = "linear"
    EASE_IN = "ease-in"
    EASE_OUT = "ease-out"
    EASE_IN_OUT = "ease-in-out"
    EASE_OUT_BOUNCE = "ease-out-bounce"
    EASE_OUT_ELASTIC = "ease-out-elastic"


def apply_easing(t: float, easing: EasingFunction) -> float:
    """
    Apply an easing function to a progress value.
    
    Args:
        t: Progress value from 0.0 to 1.0.
        easing: The easing function to apply.
        
    Returns:
        Eased progress value.
    """
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]
    
    if easing == EasingFunction.LINEAR:
        return t
    elif easing == EasingFunction.EASE_IN:
        return t * t * t
    elif easing == EasingFunction.EASE_OUT:
        return 1 - pow(1 - t, 3)
    elif easing == EasingFunction.EASE_IN_OUT:
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2
    elif easing == EasingFunction.EASE_OUT_BOUNCE:
        return _bounce_out(t)
    elif easing == EasingFunction.EASE_OUT_ELASTIC:
        return _elastic_out(t)
    
    return t


def _bounce_out(t: float) -> float:
    """Bounce out easing."""
    n1 = 7.5625
    d1 = 2.75
    
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def _elastic_out(t: float) -> float:
    """Elastic out easing."""
    if t == 0:
        return 0
    if t == 1:
        return 1
    
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


class TransitionEffect(ABC):
    """Base class for transition effects."""
    
    def __init__(
        self,
        duration: float = 0.5,
        easing: EasingFunction = EasingFunction.EASE_OUT,
    ):
        """
        Initialize the transition effect.
        
        Args:
            duration: Duration of the effect in seconds.
            easing: Easing function to use.
        """
        self.duration = duration
        self.easing = easing
    
    @abstractmethod
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """
        Apply the transition effect.
        
        Args:
            progress: Animation progress (0.0 to 1.0).
            x: Original x position.
            y: Original y position.
            opacity: Original opacity.
            
        Returns:
            Tuple of (new_x, new_y, new_opacity, scale).
        """
        pass


class FadeIn(TransitionEffect):
    """Fade in effect - element fades from transparent to opaque."""
    
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """Apply fade in effect."""
        eased = apply_easing(progress, self.easing)
        return x, y, opacity * eased, 1.0


class SlideIn(TransitionEffect):
    """Slide in effect - element slides in from a direction."""
    
    def __init__(
        self,
        duration: float = 0.5,
        easing: EasingFunction = EasingFunction.EASE_OUT,
        direction: str = "up",
        distance: float = 50,
    ):
        """
        Initialize slide in effect.
        
        Args:
            duration: Duration of the effect.
            easing: Easing function.
            direction: Direction to slide from ('up', 'down', 'left', 'right').
            distance: Distance to slide in pixels.
        """
        super().__init__(duration, easing)
        self.direction = direction
        self.distance = distance
    
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """Apply slide in effect."""
        eased = apply_easing(progress, self.easing)
        
        # Calculate offset based on direction
        offset = self.distance * (1 - eased)
        
        new_x = x
        new_y = y
        
        if self.direction == "up":
            new_y = y + offset
        elif self.direction == "down":
            new_y = y - offset
        elif self.direction == "left":
            new_x = x + offset
        elif self.direction == "right":
            new_x = x - offset
        
        return new_x, new_y, opacity * eased, 1.0


class PopIn(TransitionEffect):
    """Pop in effect - element scales up from small to full size."""
    
    def __init__(
        self,
        duration: float = 0.5,
        easing: EasingFunction = EasingFunction.EASE_OUT_ELASTIC,
        start_scale: float = 0.5,
    ):
        """
        Initialize pop in effect.
        
        Args:
            duration: Duration of the effect.
            easing: Easing function (elastic works well).
            start_scale: Starting scale factor.
        """
        super().__init__(duration, easing)
        self.start_scale = start_scale
    
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """Apply pop in effect."""
        eased = apply_easing(progress, self.easing)
        
        scale = self.start_scale + (1.0 - self.start_scale) * eased
        
        return x, y, opacity * min(1.0, eased * 1.5), scale


class ScaleIn(TransitionEffect):
    """Scale in effect - element grows from nothing."""
    
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """Apply scale in effect."""
        eased = apply_easing(progress, self.easing)
        return x, y, opacity, eased


class Combined(TransitionEffect):
    """Combine multiple effects."""
    
    def __init__(self, *effects: TransitionEffect):
        """
        Initialize combined effect.
        
        Args:
            effects: Effects to combine.
        """
        super().__init__()
        self.effects = effects
    
    def apply(
        self,
        progress: float,
        x: float,
        y: float,
        opacity: float,
    ) -> tuple[float, float, float, float]:
        """Apply all effects in sequence."""
        current_x = x
        current_y = y
        current_opacity = opacity
        current_scale = 1.0
        
        for effect in self.effects:
            new_x, new_y, new_opacity, scale = effect.apply(
                progress, current_x, current_y, current_opacity
            )
            current_x = new_x
            current_y = new_y
            current_opacity = new_opacity
            current_scale *= scale
        
        return current_x, current_y, current_opacity, current_scale

