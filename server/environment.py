"""
SOC Alert Triage Environment - Server Implementation
OpenEnv Hackathon Submission - Meta PyTorch 2026
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

from models import (
    TaskDifficulty, SecurityAlert, AlertSeverity, AlertSource,
    TriageAction, TriageObservation, TriageState, TaskConfig,
    Incident, AttackStage, Campaign, TriageActionType,
    ResponseAction
)


class SOCTriageEnvironment:
    """
    Security Operations Center (SOC) Alert Triage Environment.

    Real-world task: SOC analysts triage security alerts, correlate them into incidents,
    and detect advanced persistent threat campaigns.
    """

    def __init__(self):
        self._env_state: Optional[TriageState] = None
        self.config: Optional[TaskConfig] = None
        self.alerts: List[SecurityAlert] = []
        self.incidents: Dict[str, Incident] = {}
        self.campaigns: Dict[str, Campaign] = {}
        self.agent_incidents: Dict[str, Incident] = {}
        self.agent_campaigns: Dict[str, Campaign] = {}
        self.ground_truth_incidents: Dict[str, List[str]] = {}
        self.ground_truth_campaigns: Dict[str, Campaign] = {}
        self.investigation_cache: Dict[str, Any] = {}

    def reset(self, difficulty: TaskDifficulty = TaskDifficulty.EASY) -> TriageObservation:
        """Reset environment for new episode."""
        self._env_state = TriageState(
            episode_id=str(uuid.uuid4()),
            step_count=0,
            task_difficulty=difficulty,
            current_score=0.0
        )

        # Set task configuration
        self.config = self._get_task_config(difficulty)

        # Generate alerts and ground truth
        self.alerts = self._generate_alerts()
        self._create_ground_truth()

        # Reset agent tracking
        self.incidents = {}
        self.campaigns = {}
        self.agent_incidents = {}
        self.agent_campaigns = {}
        self.investigation_cache = {}

        return TriageObservation(
            alerts=self._get_visible_alerts(),
            incidents=[],
            campaigns=[],
            message=f"New {difficulty.value} episode started. {len(self.alerts)} alerts to process.",
            done=False,
            reward=0.0,
            metrics={"remaining_alerts": len(self.alerts)}
        )

    def step(self, action: TriageAction) -> TriageObservation:
        """Execute one step in the environment."""
        self._env_state.step_count += 1
        self._env_state.actions_history.append(action.dict())

        # Execute action based on type
        if action.action_type == TriageActionType.CLASSIFY_ALERT:
            result = self._handle_classify(action)
        elif action.action_type == TriageActionType.CREATE_INCIDENT:
            result = self._handle_create_incident(action)
        elif action.action_type == TriageActionType.ADD_TO_INCIDENT:
            result = self._handle_add_to_incident(action)
        elif action.action_type == TriageActionType.SET_ROOT_CAUSE:
            result = self._handle_set_root_cause(action)
        elif action.action_type == TriageActionType.INVESTIGATE:
            result = self._handle_investigate(action)
        elif action.action_type == TriageActionType.ESCALATE:
            result = self._handle_escalate(action)
        elif action.action_type == TriageActionType.REPORT_CAMPAIGN:
            result = self._handle_report_campaign(action)
        elif action.action_type == TriageActionType.SET_RESPONSE:
            result = self._handle_set_response(action)
        else:
            result = {"success": False, "message": "Unknown action type"}

        # Calculate reward
        reward = self._calculate_reward(action, result)

        # Check if episode is done
        done = self._check_done()

        # Update score
        self._env_state.current_score = self._calculate_score()

        # Update metrics
        self._env_state.total_alerts = len(self.alerts)
        self._env_state.alerts_classified = sum(
            1 for a in self.alerts if a.alert_id in self._get_classified_alerts()
        )
        self._env_state.incidents_created = len(self.agent_incidents)
        self._env_state.campaigns_reported = len(self.agent_campaigns)

        return TriageObservation(
            alerts=self._get_visible_alerts(),
            incidents=list(self.agent_incidents.values()),
            campaigns=list(self.agent_campaigns.values()),
            investigation_results=self.investigation_cache.get(action.alert_id) if action.alert_id else None,
            message=result.get("message", "Action executed"),
            done=done,
            reward=reward,
            metrics={
                "remaining_alerts": len(self.alerts) - self._env_state.alerts_classified,
                "current_score": self._env_state.current_score,
                "steps": self._env_state.step_count
            }
        )

    def state(self) -> TriageState:
        """Get current environment state (OpenEnv spec compliance)."""
        return self._env_state

    def _get_task_config(self, difficulty: TaskDifficulty) -> TaskConfig:
        """Get configuration for task difficulty."""
        configs = {
            TaskDifficulty.EASY: TaskConfig(
                max_steps=25,
                num_alerts=20,
                false_positive_rate=0.4,
                noise_level=0.1,
                time_span_days=1,
                require_correlation=False,
                require_campaign_detection=False
            ),
            TaskDifficulty.MEDIUM: TaskConfig(
                max_steps=60,
                num_alerts=50,
                false_positive_rate=0.5,
                noise_level=0.3,
                time_span_days=3,
                require_correlation=True,
                require_campaign_detection=False
            ),
            TaskDifficulty.HARD: TaskConfig(
                max_steps=150,
                num_alerts=200,
                false_positive_rate=0.7,
                noise_level=0.5,
                time_span_days=30,
                require_correlation=True,
                require_campaign_detection=True
            )
        }
        return configs[difficulty]

    def _generate_alerts(self) -> List[SecurityAlert]:
        """Generate synthetic security alerts."""
        alerts = []
        base_time = int(datetime.now().timestamp())

        # Alert templates for different attack patterns
        alert_templates = [
            {"type": "suspicious_login", "severity": AlertSeverity.LOW, "source": AlertSource.EMAIL},
            {"type": "malware_detected", "severity": AlertSeverity.HIGH, "source": AlertSource.ENDPOINT},
            {"type": "port_scan", "severity": AlertSeverity.MEDIUM, "source": AlertSource.FIREWALL},
            {"type": "data_exfiltration", "severity": AlertSeverity.HIGH, "source": AlertSource.CLOUD},
            {"type": "privilege_escalation", "severity": AlertSeverity.HIGH, "source": AlertSource.ENDPOINT},
            {"type": "lateral_movement", "severity": AlertSeverity.HIGH, "source": AlertSource.IDS},
            {"type": "phishing_email", "severity": AlertSeverity.MEDIUM, "source": AlertSource.EMAIL},
            {"type": "suspicious_process", "severity": AlertSeverity.MEDIUM, "source": AlertSource.ENDPOINT},
        ]

        num_alerts = self.config.num_alerts
        num_incidents = max(1, num_alerts // (5 if self._env_state.task_difficulty == TaskDifficulty.EASY else 8))

        # Create correlated incidents
        for incident_idx in range(num_incidents):
            incident_id = f"incident_{incident_idx}"
            incident_alerts = random.randint(2, 5) if self._env_state.task_difficulty != TaskDifficulty.EASY else 1

            # Determine true severity for this incident
            if random.random() < 0.3:
                true_severity = AlertSeverity.HIGH
            elif random.random() < 0.5:
                true_severity = AlertSeverity.MEDIUM
            else:
                true_severity = AlertSeverity.LOW

            for alert_idx in range(incident_alerts):
                template = random.choice(alert_templates)
                timestamp = base_time + random.randint(0, self.config.time_span_days * 86400)

                # Add noise to severity based on noise_level
                if random.random() < self.config.noise_level:
                    displayed_severity = random.choice(list(AlertSeverity))
                else:
                    displayed_severity = template["severity"]

                # Determine if this is a false positive
                is_false_positive = random.random() < self.config.false_positive_rate
                if is_false_positive:
                    true_severity = AlertSeverity.FALSE_POSITIVE

                alert = SecurityAlert(
                    alert_id=f"alert_{incident_idx}_{alert_idx}_{uuid.uuid4().hex[:8]}",
                    timestamp=timestamp,
                    source=template["source"],
                    alert_type=template["type"],
                    severity=displayed_severity,
                    source_ip=f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}",
                    dest_ip=f"10.0.{random.randint(0, 255)}.{random.randint(1, 254)}",
                    user=f"user{random.randint(1, 100)}" if random.random() > 0.3 else None,
                    asset=f"workstation{random.randint(1, 50)}" if template["source"] == AlertSource.ENDPOINT else f"server{random.randint(1, 20)}",
                    description=f"{template['type']} detected from {template['source']}",
                    raw_data={"confidence": random.uniform(0.5, 0.99)},
                    ground_truth=true_severity,
                    incident_id=incident_id
                )
                alerts.append(alert)

        # Shuffle alerts
        random.shuffle(alerts)
        return alerts

    def _create_ground_truth(self):
        """Create ground truth for grading."""
        # Group alerts by incident_id
        incident_alerts = defaultdict(list)
        for alert in self.alerts:
            if alert.incident_id:
                incident_alerts[alert.incident_id].append(alert.alert_id)

        self.ground_truth_incidents = dict(incident_alerts)

        # For hard difficulty, create campaigns
        if self._env_state.task_difficulty == TaskDifficulty.HARD:
            campaign_groups = defaultdict(list)
            for incident_id, alert_ids in incident_alerts.items():
                # Group incidents into campaigns based on timing and assets
                campaign_id = f"campaign_{hash(incident_id) % 5}"  # 5 campaigns
                campaign_groups[campaign_id].append(incident_id)

            for campaign_id, incident_ids in campaign_groups.items():
                affected_assets = set()
                for iid in incident_ids:
                    for alert in self.alerts:
                        if alert.incident_id == iid and alert.asset:
                            affected_assets.add(alert.asset)

                self.ground_truth_campaigns[campaign_id] = Campaign(
                    campaign_id=campaign_id,
                    incidents=list(incident_ids),
                    start_time=min(a.timestamp for a in self.alerts if a.incident_id in incident_ids),
                    affected_assets=list(affected_assets)
                )

    # Action handlers
    def _handle_classify(self, action: TriageAction) -> Dict[str, Any]:
        """Handle alert classification (Easy task)."""
        if not action.alert_id:
            return {"success": False, "message": "No alert_id specified"}

        alert = next((a for a in self.alerts if a.alert_id == action.alert_id), None)
        if not alert:
            return {"success": False, "message": "Alert not found"}

        if not action.classification:
            return {"success": False, "message": "No classification provided"}

        # Store classification
        self.investigation_cache[action.alert_id] = {
            "classification": action.classification,
            "confidence": action.confidence
        }

        return {
            "success": True,
            "message": f"Alert {action.alert_id} classified as {action.classification.value}"
        }

    def _handle_create_incident(self, action: TriageAction) -> Dict[str, Any]:
        """Handle incident creation (Medium/Hard task)."""
        incident_id = action.incident_id or f"agent_incident_{uuid.uuid4().hex[:8]}"

        if incident_id in self.agent_incidents:
            return {"success": False, "message": "Incident already exists"}

        self.agent_incidents[incident_id] = Incident(incident_id=incident_id)

        return {
            "success": True,
            "message": f"Created incident {incident_id}",
            "incident_id": incident_id
        }

    def _handle_add_to_incident(self, action: TriageAction) -> Dict[str, Any]:
        """Handle adding alert to incident (Medium/Hard task)."""
        if not action.incident_id or not action.alert_id:
            return {"success": False, "message": "Missing incident_id or alert_id"}

        if action.incident_id not in self.agent_incidents:
            return {"success": False, "message": "Incident not found"}

        if action.alert_id not in [a.alert_id for a in self.alerts]:
            return {"success": False, "message": "Alert not found"}

        incident = self.agent_incidents[action.incident_id]
        if action.alert_id not in incident.alerts:
            incident.alerts.append(action.alert_id)

        return {
            "success": True,
            "message": f"Added alert {action.alert_id} to incident {action.incident_id}"
        }

    def _handle_set_root_cause(self, action: TriageAction) -> Dict[str, Any]:
        """Handle setting incident root cause."""
        if not action.incident_id:
            return {"success": False, "message": "No incident_id specified"}

        if action.incident_id not in self.agent_incidents:
            return {"success": False, "message": "Incident not found"}

        self.agent_incidents[action.incident_id].root_cause = action.root_cause

        return {
            "success": True,
            "message": f"Set root cause for incident {action.incident_id}"
        }

    def _handle_investigate(self, action: TriageAction) -> Dict[str, Any]:
        """Handle investigation action (Hard task)."""
        if not action.alert_id:
            return {"success": False, "message": "No alert_id specified"}

        # Simulate investigation with partial information
        alert = next((a for a in self.alerts if a.alert_id == action.alert_id), None)
        if not alert:
            return {"success": False, "message": "Alert not found"}

        # Investigation reveals more context
        investigation_result = {
            "alert_id": action.alert_id,
            "related_alerts": [a.alert_id for a in self.alerts
                             if a.source_ip == alert.source_ip and a.alert_id != alert.alert_id][:5],
            "asset_risk_score": random.uniform(0.3, 0.9),
            "user_activity": "suspicious" if alert.user else "unknown",
            "suggested_classification": alert.ground_truth.value if alert.ground_truth else "unknown"
        }

        self.investigation_cache[action.alert_id] = investigation_result

        return {
            "success": True,
            "message": f"Investigation complete for {action.alert_id}",
            "result": investigation_result
        }

    def _handle_escalate(self, action: TriageAction) -> Dict[str, Any]:
        """Handle escalation (Hard task)."""
        return {
            "success": True,
            "message": "Escalation logged"
        }

    def _handle_report_campaign(self, action: TriageAction) -> Dict[str, Any]:
        """Handle campaign reporting (Hard task)."""
        campaign_id = action.campaign_id or f"agent_campaign_{uuid.uuid4().hex[:8]}"

        if campaign_id in self.agent_campaigns:
            return {"success": False, "message": "Campaign already exists"}

        # Find related incidents
        related_incidents = []
        if action.incident_id and action.incident_id in self.agent_incidents:
            related_incidents = [action.incident_id]

        self.agent_campaigns[campaign_id] = Campaign(
            campaign_id=campaign_id,
            incidents=related_incidents,
            start_time=int(datetime.now().timestamp())
        )

        return {
            "success": True,
            "message": f"Reported campaign {campaign_id}",
            "campaign_id": campaign_id
        }

    def _handle_set_response(self, action: TriageAction) -> Dict[str, Any]:
        """Handle setting response action."""
        return {
            "success": True,
            "message": f"Response action {action.response_action} set"
        }

    # Reward calculation
    def _calculate_reward(self, action: TriageAction, result: Dict[str, Any]) -> float:
        """Calculate reward with partial progress signals."""
        if not result.get("success"):
            return -0.1  # Penalty for failed actions

        reward = 0.0

        # Easy task: Classification rewards
        if action.action_type == TriageActionType.CLASSIFY_ALERT and action.alert_id:
            alert = next((a for a in self.alerts if a.alert_id == action.alert_id), None)
            if alert and alert.ground_truth:
                if action.classification == alert.ground_truth:
                    reward = 1.0
                else:
                    # Partial credit based on severity distance
                    severity_order = [AlertSeverity.FALSE_POSITIVE, AlertSeverity.LOW,
                                   AlertSeverity.MEDIUM, AlertSeverity.HIGH]
                    try:
                        pred_idx = severity_order.index(action.classification)
                        true_idx = severity_order.index(alert.ground_truth)
                        distance = abs(pred_idx - true_idx)
                        reward = max(0, 0.5 - (distance * 0.2))
                    except ValueError:
                        reward = 0.0

                # Penalize over-escalation
                if action.classification == AlertSeverity.HIGH and alert.ground_truth == AlertSeverity.FALSE_POSITIVE:
                    reward -= 0.5

        # Medium task: Correlation rewards
        elif action.action_type == TriageActionType.ADD_TO_INCIDENT:
            if action.alert_id and action.incident_id:
                # Check if this is a correct grouping
                ground_truth_incident = next(
                    (inc for inc, alerts in self.ground_truth_incidents.items()
                     if action.alert_id in alerts), None
                )
                if ground_truth_incident:
                    # Reward if incident contains other alerts from same ground truth
                    incident = self.agent_incidents.get(action.incident_id)
                    if incident:
                        correct_group = self.ground_truth_incidents[ground_truth_incident]
                        matches = len(set(incident.alerts) & set(correct_group))
                        if matches > 0:
                            reward = 0.5 + (matches * 0.1)

        # Hard task: Investigation and campaign rewards
        elif action.action_type == TriageActionType.INVESTIGATE:
            reward = 0.2  # Small reward for investigation

        elif action.action_type == TriageActionType.REPORT_CAMPAIGN:
            # Large reward for correct campaign detection
            if action.campaign_id:
                campaign = self.agent_campaigns.get(action.campaign_id)
                if campaign and self._check_campaign_accuracy(campaign) > 0.5:
                    reward = 3.0

        # Small step penalty to encourage efficiency
        reward -= 0.005

        return reward

    def _check_campaign_accuracy(self, campaign: Campaign) -> float:
        """Check accuracy of reported campaign against ground truth."""
        if not self.ground_truth_campaigns:
            return 0.0

        best_match = 0.0
        for gt_campaign in self.ground_truth_campaigns.values():
            # Calculate Jaccard similarity of incidents
            agent_set = set(campaign.incidents)
            gt_set = set(gt_campaign.incidents)
            if agent_set or gt_set:
                intersection = len(agent_set & gt_set)
                union = len(agent_set | gt_set)
                similarity = intersection / union if union > 0 else 0
                best_match = max(best_match, similarity)

        return best_match

    def _check_done(self) -> bool:
        """Check if episode is complete."""
        if self._env_state.step_count >= self.config.max_steps:
            return True

        # For easy task: done when all alerts classified
        if self._env_state.task_difficulty == TaskDifficulty.EASY:
            classified = len([k for k in self.investigation_cache.keys()
                           if any(a.alert_id == k for a in self.alerts)])
            if classified >= len(self.alerts):
                return True

        # For medium task: done when incidents created and populated
        if self._env_state.task_difficulty == TaskDifficulty.MEDIUM:
            if self.agent_incidents and self._env_state.step_count > self.config.max_steps * 0.8:
                return True

        return False

    def _calculate_score(self) -> float:
        """Calculate current grader score (0.0-1.0)."""
        if self._env_state.task_difficulty == TaskDifficulty.EASY:
            return self._calculate_easy_score()
        elif self._env_state.task_difficulty == TaskDifficulty.MEDIUM:
            return self._calculate_medium_score()
        else:
            return self._calculate_hard_score()

    def _calculate_easy_score(self) -> float:
        """Calculate score for easy task (classification accuracy)."""
        correct = 0
        total = 0

        for alert in self.alerts:
            classification = self.investigation_cache.get(alert.alert_id, {}).get("classification")
            if classification and alert.ground_truth:
                total += 1
                if classification == alert.ground_truth:
                    correct += 1

        if total == 0:
            return 0.0

        accuracy = correct / total

        # Penalize over-escalation
        high_classifications = sum(
            1 for a in self.alerts
            if self.investigation_cache.get(a.alert_id, {}).get("classification") == AlertSeverity.HIGH
        )
        true_high = sum(1 for a in self.alerts if a.ground_truth == AlertSeverity.HIGH)
        if high_classifications > max(1, true_high * 1.5):
            accuracy *= 0.8  # Penalty

        return round(accuracy, 4)

    def _calculate_medium_score(self) -> float:
        """Calculate score for medium task (correlation F1 score)."""
        if not self.agent_incidents:
            return 0.0

        # Calculate precision and recall
        total_precision = 0.0
        total_recall = 0.0

        for agent_incident in self.agent_incidents.values():
            # Find best matching ground truth incident
            best_precision = 0.0
            best_recall = 0.0

            for gt_incident, gt_alerts in self.ground_truth_incidents.items():
                if agent_incident.alerts:
                    intersection = len(set(agent_incident.alerts) & set(gt_alerts))
                    precision = intersection / len(agent_incident.alerts)
                    recall = intersection / len(gt_alerts) if gt_alerts else 0
                    best_precision = max(best_precision, precision)
                    best_recall = max(best_recall, recall)

            total_precision += best_precision
            total_recall += best_recall

        avg_precision = total_precision / len(self.agent_incidents) if self.agent_incidents else 0
        avg_recall = total_recall / len(self.ground_truth_incidents) if self.ground_truth_incidents else 0

        f1 = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0

        return round(f1, 4)

    def _calculate_hard_score(self) -> float:
        """Calculate score for hard task (multi-factor)."""
        scores = []

        # Campaign detection (25%)
        if self.ground_truth_campaigns and self.agent_campaigns:
            campaign_scores = []
            for agent_campaign in self.agent_campaigns.values():
                campaign_scores.append(self._check_campaign_accuracy(agent_campaign))
            scores.append(0.25 * (max(campaign_scores) if campaign_scores else 0))
        else:
            scores.append(0.0)

        # Incident correlation quality (25%)
        correlation_score = self._calculate_medium_score() * 0.25
        scores.append(correlation_score)

        # Classification accuracy (20%)
        classification_score = self._calculate_easy_score() * 0.20
        scores.append(classification_score)

        # Investigation efficiency (15%)
        investigation_score = min(1.0, len(self.investigation_cache) / max(1, len(self.alerts) * 0.5)) * 0.15
        scores.append(investigation_score)

        # Response appropriateness (15%)
        # Check if high severity alerts were escalated
        response_score = 0.15  # Base score
        for alert in self.alerts:
            if alert.ground_truth in [AlertSeverity.HIGH, AlertSeverity.MEDIUM]:
                if alert.alert_id in self.investigation_cache:
                    response_score += 0.01
        scores.append(min(0.15, response_score))

        return round(sum(scores), 4)

    def _get_visible_alerts(self) -> List[SecurityAlert]:
        """Get alerts visible to the agent."""
        # Return unclassified alerts first
        unclassified = [a for a in self.alerts
                       if a.alert_id not in self.investigation_cache]
        return unclassified[:10]  # Limit visible alerts

    def _get_classified_alerts(self) -> List[str]:
        """Get list of classified alert IDs."""
        return [k for k in self.investigation_cache.keys()
                if any(a.alert_id == k for a in self.alerts)]
