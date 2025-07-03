"""
Human interface for operator communication and control
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages to/from human operators"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    ACKNOWLEDGMENT = "acknowledgment"


class OperatorRole(Enum):
    """Operator roles and permissions"""
    VIEWER = "viewer"           # Read-only access
    OPERATOR = "operator"       # Basic control
    SUPERVISOR = "supervisor"   # Advanced control
    EMERGENCY = "emergency"     # Emergency override


@dataclass
class HumanMessage:
    """Message to/from human operator"""
    message_id: str
    message_type: MessageType
    content: str
    sender: str                 # operator_id or "system"
    recipient: str              # operator_id or "system"
    timestamp: datetime
    priority: int = 1           # 1=low, 5=critical
    requires_response: bool = False
    metadata: Optional[Dict] = None


@dataclass
class OperatorSession:
    """Active operator session"""
    operator_id: str
    role: OperatorRole
    login_time: datetime
    last_activity: datetime
    is_active: bool = True
    location: Optional[str] = None
    contact_info: Optional[Dict] = None


class HumanInterface:
    """
    Human interface system for nuclear facility operations
    
    Provides secure communication between the robotic system and human operators,
    with role-based access control and emergency protocols.
    """
    
    def __init__(self):
        self.active_sessions = {}  # operator_id -> OperatorSession
        self.message_history = []
        self.pending_messages = {}  # operator_id -> List[HumanMessage]
        self.command_callbacks = {}  # command_type -> callback
        self.response_callbacks = {}  # message_id -> callback
        
        # Authentication and authorization
        self.operator_credentials = {}  # operator_id -> credentials
        self.role_permissions = {
            OperatorRole.VIEWER: {
                'can_view_status', 'can_view_logs'
            },
            OperatorRole.OPERATOR: {
                'can_view_status', 'can_view_logs', 'can_control_robot',
                'can_acknowledge_alerts', 'can_modify_thresholds'
            },
            OperatorRole.SUPERVISOR: {
                'can_view_status', 'can_view_logs', 'can_control_robot',
                'can_acknowledge_alerts', 'can_modify_thresholds',
                'can_emergency_stop', 'can_reset_emergency', 'can_manage_operators'
            },
            OperatorRole.EMERGENCY: {
                'can_view_status', 'can_view_logs', 'can_control_robot',
                'can_acknowledge_alerts', 'can_modify_thresholds',
                'can_emergency_stop', 'can_reset_emergency', 'can_manage_operators',
                'can_override_safety', 'can_emergency_command'
            }
        }
        
        # Communication settings
        self.session_timeout = 3600  # 1 hour
        self.max_message_history = 10000
        self.auto_escalate_timeout = 300  # 5 minutes
        
        logger.info("Human interface system initialized")
    
    async def authenticate_operator(self, 
                                  operator_id: str, 
                                  credentials: Dict) -> Optional[OperatorSession]:
        """
        Authenticate operator and create session
        
        Args:
            operator_id: Unique operator identifier
            credentials: Authentication credentials
            
        Returns:
            OperatorSession if authentication successful, None otherwise
        """
        try:
            # In production, would validate against secure credential store
            # For demo, simple credential check
            stored_creds = self.operator_credentials.get(operator_id)
            
            if not stored_creds:
                logger.warning(f"Authentication failed: unknown operator {operator_id}")
                return None
            
            # Simplified credential validation
            if credentials.get('password') != stored_creds.get('password'):
                logger.warning(f"Authentication failed: invalid credentials for {operator_id}")
                return None
            
            # Create session
            session = OperatorSession(
                operator_id=operator_id,
                role=OperatorRole(stored_creds.get('role', 'viewer')),
                login_time=datetime.now(),
                last_activity=datetime.now(),
                location=credentials.get('location'),
                contact_info=credentials.get('contact_info')
            )
            
            self.active_sessions[operator_id] = session
            
            # Send welcome message
            await self.send_message_to_operator(
                operator_id,
                MessageType.INFO,
                f"Welcome {operator_id}. You are logged in with {session.role.value} privileges.",
                priority=2
            )
            
            logger.info(f"Operator {operator_id} authenticated with role {session.role.value}")
            return session
            
        except Exception as e:
            logger.error(f"Error authenticating operator {operator_id}: {e}")
            return None
    
    async def logout_operator(self, operator_id: str):
        """Logout operator and close session"""
        if operator_id in self.active_sessions:
            session = self.active_sessions[operator_id]
            session.is_active = False
            
            await self.send_message_to_operator(
                operator_id,
                MessageType.INFO,
                "You have been logged out. Session ended.",
                priority=1
            )
            
            del self.active_sessions[operator_id]
            logger.info(f"Operator {operator_id} logged out")
    
    def add_operator_credentials(self, 
                               operator_id: str, 
                               password: str, 
                               role: OperatorRole,
                               contact_info: Optional[Dict] = None):
        """Add operator credentials to system"""
        self.operator_credentials[operator_id] = {
            'password': password,
            'role': role.value,
            'contact_info': contact_info or {},
            'created': datetime.now()
        }
        logger.info(f"Added credentials for operator {operator_id} with role {role.value}")
    
    async def send_message_to_operator(self,
                                     operator_id: str,
                                     message_type: MessageType,
                                     content: str,
                                     priority: int = 1,
                                     requires_response: bool = False,
                                     metadata: Optional[Dict] = None) -> str:
        """Send message to specific operator"""
        message_id = f"msg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.message_history)}"
        
        message = HumanMessage(
            message_id=message_id,
            message_type=message_type,
            content=content,
            sender="system",
            recipient=operator_id,
            timestamp=datetime.now(),
            priority=priority,
            requires_response=requires_response,
            metadata=metadata
        )
        
        # Store message
        self.message_history.append(message)
        
        # Add to pending messages for operator
        if operator_id not in self.pending_messages:
            self.pending_messages[operator_id] = []
        self.pending_messages[operator_id].append(message)
        
        # Update operator activity
        if operator_id in self.active_sessions:
            self.active_sessions[operator_id].last_activity = datetime.now()
        
        logger.info(f"Message sent to {operator_id}: {message_type.value} - {content[:50]}...")
        
        # Auto-escalate critical messages
        if priority >= 4:
            await self._escalate_message(message)
        
        return message_id
    
    async def broadcast_message(self,
                              message_type: MessageType,
                              content: str,
                              priority: int = 1,
                              role_filter: Optional[OperatorRole] = None) -> List[str]:
        """Broadcast message to all active operators or specific role"""
        message_ids = []
        
        for operator_id, session in self.active_sessions.items():
            if session.is_active:
                # Filter by role if specified
                if role_filter and session.role != role_filter:
                    continue
                
                message_id = await self.send_message_to_operator(
                    operator_id, message_type, content, priority
                )
                message_ids.append(message_id)
        
        return message_ids
    
    async def receive_message_from_operator(self,
                                          operator_id: str,
                                          message_type: MessageType,
                                          content: str,
                                          reply_to: Optional[str] = None,
                                          metadata: Optional[Dict] = None) -> str:
        """Receive message from operator"""
        # Verify operator is authenticated
        if operator_id not in self.active_sessions:
            raise ValueError(f"Operator {operator_id} not authenticated")
        
        session = self.active_sessions[operator_id]
        if not session.is_active:
            raise ValueError(f"Operator {operator_id} session inactive")
        
        message_id = f"op_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.message_history)}"
        
        message = HumanMessage(
            message_id=message_id,
            message_type=message_type,
            content=content,
            sender=operator_id,
            recipient="system",
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Store message
        self.message_history.append(message)
        session.last_activity = datetime.now()
        
        # Process message based on type
        if message_type == MessageType.COMMAND:
            await self._process_operator_command(operator_id, content, metadata)
        elif message_type == MessageType.RESPONSE and reply_to:
            await self._process_operator_response(reply_to, content)
        elif message_type == MessageType.ACKNOWLEDGMENT:
            await self._process_acknowledgment(operator_id, content)
        
        logger.info(f"Message received from {operator_id}: {message_type.value} - {content[:50]}...")
        
        return message_id
    
    async def _process_operator_command(self, 
                                      operator_id: str, 
                                      command: str, 
                                      metadata: Optional[Dict]):
        """Process command from operator"""
        session = self.active_sessions[operator_id]
        
        try:
            # Parse command
            if metadata and 'command_type' in metadata:
                command_type = metadata['command_type']
            else:
                # Simple command parsing
                parts = command.split()
                command_type = parts[0].lower() if parts else "unknown"
            
            # Check permissions
            required_permission = self._get_command_permission(command_type)
            if required_permission and not self._has_permission(session.role, required_permission):
                await self.send_message_to_operator(
                    operator_id,
                    MessageType.ERROR,
                    f"Insufficient permissions for command: {command_type}",
                    priority=3
                )
                return
            
            # Execute command callback
            if command_type in self.command_callbacks:
                callback = self.command_callbacks[command_type]
                try:
                    if asyncio.iscoroutinefunction(callback):
                        result = await callback(operator_id, command, metadata)
                    else:
                        result = callback(operator_id, command, metadata)
                    
                    # Send confirmation
                    await self.send_message_to_operator(
                        operator_id,
                        MessageType.RESPONSE,
                        f"Command executed: {command_type}. Result: {result}",
                        priority=2
                    )
                    
                except Exception as e:
                    await self.send_message_to_operator(
                        operator_id,
                        MessageType.ERROR,
                        f"Command execution failed: {e}",
                        priority=3
                    )
            else:
                await self.send_message_to_operator(
                    operator_id,
                    MessageType.ERROR,
                    f"Unknown command: {command_type}",
                    priority=2
                )
                
        except Exception as e:
            logger.error(f"Error processing command from {operator_id}: {e}")
    
    async def _process_operator_response(self, reply_to: str, content: str):
        """Process response from operator"""
        if reply_to in self.response_callbacks:
            callback = self.response_callbacks[reply_to]
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(content)
                else:
                    callback(content)
                # Remove callback after use
                del self.response_callbacks[reply_to]
            except Exception as e:
                logger.error(f"Error in response callback: {e}")
    
    async def _process_acknowledgment(self, operator_id: str, content: str):
        """Process acknowledgment from operator"""
        # Mark pending messages as acknowledged
        if operator_id in self.pending_messages:
            # Simple acknowledgment processing
            ack_count = len(self.pending_messages[operator_id])
            self.pending_messages[operator_id] = []
            
            logger.info(f"Operator {operator_id} acknowledged {ack_count} messages")
    
    def _get_command_permission(self, command_type: str) -> Optional[str]:
        """Get required permission for command type"""
        command_permissions = {
            'stop': 'can_control_robot',
            'start': 'can_control_robot',
            'emergency_stop': 'can_emergency_stop',
            'reset_emergency': 'can_reset_emergency',
            'set_threshold': 'can_modify_thresholds',
            'override_safety': 'can_override_safety',
            'status': 'can_view_status',
            'logs': 'can_view_logs'
        }
        return command_permissions.get(command_type)
    
    def _has_permission(self, role: OperatorRole, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in self.role_permissions.get(role, set())
    
    async def _escalate_message(self, message: HumanMessage):
        """Escalate critical message to supervisors"""
        for operator_id, session in self.active_sessions.items():
            if (session.is_active and 
                session.role in [OperatorRole.SUPERVISOR, OperatorRole.EMERGENCY]):
                
                escalated_content = f"ESCALATED: {message.content}"
                await self.send_message_to_operator(
                    operator_id,
                    MessageType.CRITICAL,
                    escalated_content,
                    priority=5,
                    requires_response=True
                )
    
    def register_command_callback(self, command_type: str, callback: Callable):
        """Register callback for specific command type"""
        self.command_callbacks[command_type] = callback
    
    def register_response_callback(self, message_id: str, callback: Callable):
        """Register callback for message response"""
        self.response_callbacks[message_id] = callback
    
    async def cleanup_inactive_sessions(self):
        """Clean up inactive operator sessions"""
        current_time = datetime.now()
        inactive_operators = []
        
        for operator_id, session in self.active_sessions.items():
            time_since_activity = (current_time - session.last_activity).total_seconds()
            if time_since_activity > self.session_timeout:
                inactive_operators.append(operator_id)
        
        for operator_id in inactive_operators:
            await self.logout_operator(operator_id)
            logger.info(f"Operator {operator_id} session timed out")
    
    def get_pending_messages(self, operator_id: str) -> List[HumanMessage]:
        """Get pending messages for operator"""
        return self.pending_messages.get(operator_id, []).copy()
    
    def get_active_operators(self) -> List[Dict]:
        """Get list of active operators"""
        active_ops = []
        for operator_id, session in self.active_sessions.items():
            if session.is_active:
                active_ops.append({
                    'operator_id': operator_id,
                    'role': session.role.value,
                    'login_time': session.login_time,
                    'last_activity': session.last_activity,
                    'location': session.location
                })
        return active_ops
    
    def get_message_history(self, 
                          start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          operator_id: Optional[str] = None) -> List[HumanMessage]:
        """Get message history with optional filters"""
        filtered_messages = []
        
        for message in self.message_history:
            # Time filter
            if start_time and message.timestamp < start_time:
                continue
            if end_time and message.timestamp > end_time:
                continue
            
            # Operator filter
            if operator_id and message.sender != operator_id and message.recipient != operator_id:
                continue
            
            filtered_messages.append(message)
        
        return filtered_messages
    
    async def emergency_broadcast(self, content: str, metadata: Optional[Dict] = None):
        """Send emergency broadcast to all operators"""
        await self.broadcast_message(
            MessageType.CRITICAL,
            f"EMERGENCY: {content}",
            priority=5
        )
        
        # Also escalate to emergency role operators
        for operator_id, session in self.active_sessions.items():
            if session.is_active and session.role == OperatorRole.EMERGENCY:
                await self.send_message_to_operator(
                    operator_id,
                    MessageType.CRITICAL,
                    f"EMERGENCY ALERT: {content}",
                    priority=5,
                    requires_response=True,
                    metadata=metadata
                )
    
    def export_communications_log(self, 
                                start_time: datetime, 
                                end_time: datetime) -> List[Dict]:
        """Export communications log for audit purposes"""
        log_entries = []
        
        for message in self.message_history:
            if start_time <= message.timestamp <= end_time:
                log_entries.append({
                    'message_id': message.message_id,
                    'type': message.message_type.value,
                    'sender': message.sender,
                    'recipient': message.recipient,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat(),
                    'priority': message.priority,
                    'requires_response': message.requires_response,
                    'metadata': message.metadata
                })
        
        return log_entries