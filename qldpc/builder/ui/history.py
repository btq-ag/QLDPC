"""
Command history for undo/redo functionality.

This module implements the Command pattern for tracking and reversing
user actions in the circuit builder.
Author: Jeffrey Morais"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Any, TYPE_CHECKING
import copy

if TYPE_CHECKING:
    from ..components import Component3D


class Command(ABC):
    """Abstract base class for undoable commands."""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command. Returns True if successful."""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command. Returns True if successful."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the command."""
        pass


class PlaceComponentCommand(Command):
    """Command for placing a component on the circuit."""
    
    def __init__(self, component: 'Component3D', components_list: List['Component3D']):
        """
        Initialize the place command.
        
        Args:
            component: The component to place
            components_list: Reference to the main components list
        """
        self.component = component
        self.components_list = components_list
    
    def execute(self) -> bool:
        """Add the component to the list."""
        if self.component not in self.components_list:
            self.components_list.append(self.component)
            return True
        return False
    
    def undo(self) -> bool:
        """Remove the component from the list."""
        if self.component in self.components_list:
            self.components_list.remove(self.component)
            return True
        return False
    
    @property
    def description(self) -> str:
        return f"Place {self.component.component_type.value} at {self.component.position}"


class DeleteComponentCommand(Command):
    """Command for deleting a component from the circuit."""
    
    def __init__(self, component: 'Component3D', components_list: List['Component3D']):
        """
        Initialize the delete command.
        
        Args:
            component: The component to delete
            components_list: Reference to the main components list
        """
        self.component = component
        self.components_list = components_list
        self.index = -1  # Will store the original index for proper restoration
    
    def execute(self) -> bool:
        """Remove the component from the list."""
        if self.component in self.components_list:
            self.index = self.components_list.index(self.component)
            self.components_list.remove(self.component)
            return True
        return False
    
    def undo(self) -> bool:
        """Restore the component to the list."""
        if self.component not in self.components_list:
            if self.index >= 0 and self.index <= len(self.components_list):
                self.components_list.insert(self.index, self.component)
            else:
                self.components_list.append(self.component)
            return True
        return False
    
    @property
    def description(self) -> str:
        return f"Delete {self.component.component_type.value}"


class MoveComponentCommand(Command):
    """Command for moving a component to a new position."""
    
    def __init__(self, component: 'Component3D', old_position: tuple, new_position: tuple):
        """
        Initialize the move command.
        
        Args:
            component: The component to move
            old_position: Original position (x, y, z)
            new_position: New position (x, y, z)
        """
        self.component = component
        self.old_position = old_position
        self.new_position = new_position
    
    def execute(self) -> bool:
        """Move to new position."""
        self.component.position = self.new_position
        return True
    
    def undo(self) -> bool:
        """Move back to old position."""
        self.component.position = self.old_position
        return True
    
    @property
    def description(self) -> str:
        return f"Move {self.component.component_type.value} from {self.old_position} to {self.new_position}"


class RotateComponentCommand(Command):
    """Command for rotating a component."""
    
    def __init__(self, component: 'Component3D', old_rotation: float, new_rotation: float):
        """
        Initialize the rotate command.
        
        Args:
            component: The component to rotate
            old_rotation: Original rotation in degrees
            new_rotation: New rotation in degrees
        """
        self.component = component
        self.old_rotation = old_rotation
        self.new_rotation = new_rotation
    
    def execute(self) -> bool:
        """Apply new rotation."""
        self.component.rotation = self.new_rotation
        return True
    
    def undo(self) -> bool:
        """Restore old rotation."""
        self.component.rotation = self.old_rotation
        return True
    
    @property
    def description(self) -> str:
        return f"Rotate {self.component.component_type.value} to {self.new_rotation}°"


class BatchCommand(Command):
    """Command that groups multiple commands together."""
    
    def __init__(self, commands: List[Command], description_text: str = "Batch operation"):
        """
        Initialize the batch command.
        
        Args:
            commands: List of commands to execute together
            description_text: Description for the batch
        """
        self.commands = commands
        self._description = description_text
    
    def execute(self) -> bool:
        """Execute all commands in order."""
        success = True
        for cmd in self.commands:
            if not cmd.execute():
                success = False
        return success
    
    def undo(self) -> bool:
        """Undo all commands in reverse order."""
        success = True
        for cmd in reversed(self.commands):
            if not cmd.undo():
                success = False
        return success
    
    @property
    def description(self) -> str:
        return self._description


class CommandHistory:
    """
    Manages command history for undo/redo functionality.
    
    Implements a standard undo/redo stack with a configurable maximum size.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize the command history.
        
        Args:
            max_size: Maximum number of commands to keep in history
        """
        self.max_size = max_size
        self._history: List[Command] = []
        self._current_index: int = -1  # Points to the last executed command
    
    def execute(self, command: Command) -> bool:
        """
        Execute a command and add it to history.
        
        Args:
            command: The command to execute
            
        Returns:
            True if the command was executed successfully
        """
        if command.execute():
            # Clear any redo history
            self._history = self._history[:self._current_index + 1]
            
            # Add new command
            self._history.append(command)
            self._current_index += 1
            
            # Trim if exceeds max size
            if len(self._history) > self.max_size:
                self._history.pop(0)
                self._current_index -= 1
            
            return True
        return False
    
    def undo(self) -> Optional[Command]:
        """
        Undo the last command.
        
        Returns:
            The undone command, or None if nothing to undo
        """
        if self.can_undo:
            command = self._history[self._current_index]
            if command.undo():
                self._current_index -= 1
                return command
        return None
    
    def redo(self) -> Optional[Command]:
        """
        Redo the last undone command.
        
        Returns:
            The redone command, or None if nothing to redo
        """
        if self.can_redo:
            self._current_index += 1
            command = self._history[self._current_index]
            if command.execute():
                return command
            else:
                self._current_index -= 1
        return None
    
    @property
    def can_undo(self) -> bool:
        """Check if there are commands to undo."""
        return self._current_index >= 0
    
    @property
    def can_redo(self) -> bool:
        """Check if there are commands to redo."""
        return self._current_index < len(self._history) - 1
    
    @property
    def undo_description(self) -> Optional[str]:
        """Get description of the next command to undo."""
        if self.can_undo:
            return self._history[self._current_index].description
        return None
    
    @property
    def redo_description(self) -> Optional[str]:
        """Get description of the next command to redo."""
        if self.can_redo:
            return self._history[self._current_index + 1].description
        return None
    
    def clear(self):
        """Clear all history."""
        self._history.clear()
        self._current_index = -1
    
    def __len__(self) -> int:
        """Return the number of commands in history."""
        return len(self._history)
