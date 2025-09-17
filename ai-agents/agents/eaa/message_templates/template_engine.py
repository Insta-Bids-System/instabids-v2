"""
Template Engine for EAA
Dynamic message generation based on project type and contractor info
"""
from datetime import datetime
from typing import Any


class TemplateEngine:
    """Dynamic message template engine for contractor outreach"""

    def __init__(self):
        """Initialize template engine with project-specific templates"""
        self.email_templates = self._load_email_templates()
        self.sms_templates = self._load_sms_templates()

        print("[TemplateEngine] Initialized with project-specific templates")

    def generate_messages(self, contractor: dict[str, Any], bid_card_data: dict[str, Any],
                         channels: list[str], urgency: str) -> dict[str, dict[str, Any]]:
        """
        Generate personalized messages for all requested channels

        Args:
            contractor: Contractor information
            bid_card_data: Project details from bid card
            channels: List of channels to generate for
            urgency: Project urgency level

        Returns:
            Dictionary with channel-specific message data
        """
        try:
            messages = {}

            # Prepare template variables
            template_vars = self._prepare_template_variables(
                contractor, bid_card_data, urgency
            )

            # Generate email message
            if "email" in channels:
                messages["email"] = self._generate_email_message(
                    template_vars, bid_card_data["project_type"], urgency
                )

            # Generate SMS message
            if "sms" in channels:
                messages["sms"] = self._generate_sms_message(
                    template_vars, bid_card_data["project_type"], urgency
                )

            print(f"[TemplateEngine] Generated messages for {len(messages)} channels")
            return messages

        except Exception as e:
            print(f"[TemplateEngine ERROR] Failed to generate messages: {e}")
            return {}

    def _prepare_template_variables(self, contractor: dict[str, Any],
                                   bid_card_data: dict[str, Any], urgency: str) -> dict[str, Any]:
        """Prepare variables for template substitution"""

        # Extract contractor info
        contractor_name = contractor.get("contact_name", contractor.get("company_name", "there"))
        company_name = contractor.get("company_name", "your company")

        # Extract project details
        project_type = bid_card_data.get("project_type", "home improvement")

        # Handle location - check both top level and nested in bid_document
        location_data = bid_card_data.get("location")
        if not location_data and bid_card_data.get("bid_document"):
            # Try to get from nested bid_document structure
            all_data = bid_card_data.get("bid_document", {}).get("all_extracted_data", {})
            location_data = all_data.get("location")

        if not location_data:
            location_data = "your area"
        if isinstance(location_data, dict):
            # Extract location string from object
            city = location_data.get("city", "")
            state = location_data.get("state", "")
            zip_code = location_data.get("zip_code", "")
            if city and state:
                location = f"{city}, {state}"
                if zip_code:
                    location += f" {zip_code}"
            else:
                location = location_data.get("full_location", location_data.get("address", "your area"))
        else:
            location = location_data

        budget_min = bid_card_data.get("budget_min", 5000)
        budget_max = bid_card_data.get("budget_max", 15000)
        scope_summary = bid_card_data.get("scope_summary", "quality work needed")

        # NEW: Extract deadline information for template context
        deadline_context = ""
        deadline_urgency_modifier = ""
        
        # Check for exact deadline fields from the date extraction system
        project_completion_deadline = bid_card_data.get("project_completion_deadline")
        bid_collection_deadline = bid_card_data.get("bid_collection_deadline") 
        deadline_hard = bid_card_data.get("deadline_hard", False)
        deadline_context_raw = bid_card_data.get("deadline_context", "")
        
        if project_completion_deadline:
            from datetime import datetime
            try:
                if isinstance(project_completion_deadline, str):
                    deadline_date = datetime.fromisoformat(project_completion_deadline.replace('Z', '+00:00'))
                else:
                    deadline_date = project_completion_deadline
                    
                days_remaining = (deadline_date - datetime.now()).days
                
                # Create deadline context for contractor messages
                if deadline_hard:
                    deadline_urgency_modifier = "FIRM DEADLINE - "
                    deadline_context = f"This project has a firm deadline of {deadline_date.strftime('%B %d')}."
                else:
                    deadline_context = f"The homeowner is hoping to complete this by {deadline_date.strftime('%B %d')}."
                
                # Add urgency context based on days remaining
                if days_remaining <= 3:
                    deadline_context += " This is an urgent timeline requiring immediate attention."
                elif days_remaining <= 7:
                    deadline_context += " Time is of the essence for this project."
                elif days_remaining <= 14:
                    deadline_context += " Please respond promptly to meet this timeline."
                    
                # If we have deadline context from CIA, include that too
                if deadline_context_raw:
                    deadline_context += f" Context: {deadline_context_raw}"
                    
            except Exception as e:
                print(f"[TemplateEngine] Error parsing deadline: {e}")

        # Generate urgency-specific content
        urgency_prefix, urgency_text = self._get_urgency_content(urgency)

        # Create bid card link to external landing page
        # Using the bid card ID as a public token for now
        # In production, bid cards should have a separate public_token field
        bid_card_id = bid_card_data.get('id', 'demo')
        bid_card_link = f"https://instabids.com/join?bid={bid_card_id}&src=email"

        template_vars = {
            "contractor_name": contractor_name,
            "company_name": company_name,
            "project_type": project_type.title(),
            "location": location,
            "budget_min": f"{budget_min:,}",
            "budget_max": f"{budget_max:,}",
            "scope_summary": scope_summary,
            "urgency_level": urgency,
            "urgency_prefix": urgency_prefix,
            "urgency_text": urgency_text,
            "deadline_context": deadline_context,
            "deadline_urgency_modifier": deadline_urgency_modifier,
            "bid_card_link": bid_card_link,
            "current_date": datetime.now().strftime("%B %d, %Y"),
            "timeline": self._get_timeline_text(urgency)
        }

        return template_vars

    def _generate_email_message(self, template_vars: dict[str, Any],
                               project_type: str, urgency: str) -> dict[str, Any]:
        """Generate personalized email message"""

        # Select appropriate template
        template_key = self._select_email_template(project_type, urgency)
        template = self.email_templates[template_key]

        # Generate subject line
        subject = self._substitute_variables(template["subject"], template_vars)

        # Generate HTML content
        html_content = self._substitute_variables(template["html_body"], template_vars)

        # Generate plain text version
        plain_content = self._substitute_variables(template["plain_body"], template_vars)

        return {
            "subject": subject,
            "html_content": html_content,
            "plain_content": plain_content,
            "template_used": template_key,
            "personalization_score": self._calculate_personalization_score(template_vars)
        }

    def _generate_sms_message(self, template_vars: dict[str, Any],
                             project_type: str, urgency: str) -> dict[str, Any]:
        """Generate personalized SMS message"""

        # Select appropriate template
        template_key = self._select_sms_template(project_type, urgency)
        template = self.sms_templates[template_key]

        # Generate SMS content
        content = self._substitute_variables(template["content"], template_vars)

        # Ensure SMS is under 160 characters if possible
        if len(content) > 160:
            content = self._truncate_sms(content)

        return {
            "content": content,
            "character_count": len(content),
            "template_used": template_key,
            "truncated": len(content) > 160
        }

    def _select_email_template(self, project_type: str, urgency: str) -> str:
        """Select appropriate email template"""
        project_lower = project_type.lower()

        if urgency == "emergency":
            if "kitchen" in project_lower:
                return "kitchen_urgent_email"
            elif "bathroom" in project_lower:
                return "bathroom_urgent_email"
            elif "roof" in project_lower:
                return "roofing_urgent_email"
            elif "mold" in project_lower:
                return "mold_urgent_email"
            else:
                return "general_urgent_email"
        else:
            if "kitchen" in project_lower:
                return "kitchen_standard_email"
            elif "bathroom" in project_lower:
                return "bathroom_standard_email"
            elif "roof" in project_lower:
                return "roofing_standard_email"
            elif "mold" in project_lower:
                return "mold_standard_email"
            else:
                return "general_standard_email"

    def _select_sms_template(self, project_type: str, urgency: str) -> str:
        """Select appropriate SMS template"""
        project_lower = project_type.lower()

        if urgency == "emergency":
            return "urgent_sms"
        elif "kitchen" in project_lower:
            return "kitchen_sms"
        elif "bathroom" in project_lower:
            return "bathroom_sms"
        elif "roof" in project_lower:
            return "roofing_sms"
        else:
            return "general_sms"

    def _substitute_variables(self, template: str, variables: dict[str, Any]) -> str:
        """Replace template variables with actual values"""
        result = template

        for key, value in variables.items():
            placeholder = f"{{{key}}}"
            result = result.replace(placeholder, str(value))

        return result

    def _get_urgency_content(self, urgency: str) -> tuple:
        """Get urgency-specific content"""
        if urgency == "emergency":
            return "URGENT: ", "This is an emergency project that needs immediate attention."
        elif urgency == "week":
            return "TIME-SENSITIVE: ", "This project needs to start within the next week."
        elif urgency == "month":
            return "", "This project is planned to start within the next month."
        else:
            return "", "This is a flexible timeline project."

    def _get_timeline_text(self, urgency: str) -> str:
        """Get timeline description"""
        if urgency == "emergency":
            return "ASAP - within 24-48 hours"
        elif urgency == "week":
            return "Start within 1 week"
        elif urgency == "month":
            return "Start within 1 month"
        else:
            return "Flexible timeline"

    def _calculate_personalization_score(self, template_vars: dict[str, Any]) -> float:
        """Calculate how personalized the message is"""
        score = 0.0

        # Base score for having contractor name
        if template_vars.get("contractor_name") != "there":
            score += 30

        # Score for specific project type
        if template_vars.get("project_type") != "Home Improvement":
            score += 25

        # Score for specific location
        if template_vars.get("location") != "your area":
            score += 20

        # Score for budget range
        if template_vars.get("budget_min") != "5,000":
            score += 15

        # Score for urgency specificity
        if template_vars.get("urgency_level") != "flexible":
            score += 10

        return min(100.0, score)

    def _truncate_sms(self, content: str) -> str:
        """Truncate SMS content while preserving important info"""
        if len(content) <= 160:
            return content

        # Try to preserve the call-to-action
        if "Reply YES" in content:
            # Keep the CTA and truncate the middle
            parts = content.split("Reply YES")
            if len(parts) == 2:
                available_length = 160 - len("Reply YES" + parts[1])
                truncated_start = parts[0][:available_length-3] + "..."
                return truncated_start + "Reply YES" + parts[1]

        # Simple truncation
        return content[:157] + "..."

    def _load_email_templates(self) -> dict[str, dict[str, str]]:
        """Load email templates for different project types"""
        return {
            "kitchen_urgent_email": {
                "subject": "{deadline_urgency_modifier}{urgency_prefix}Kitchen Remodel Project in {location} - ${budget_min}-${budget_max}",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #d32f2f;">{urgency_prefix}Kitchen Remodel Opportunity</h2>

                    <p>Hi {contractor_name},</p>

                    <p>We have an <strong>{urgency_level}</strong> kitchen remodeling project in <strong>{location}</strong> that perfectly matches your expertise in kitchen renovations.</p>

                    <div style="background: #f5f5f5; padding: 15px; margin: 20px 0; border-left: 4px solid #2196f3;">
                        <h3 style="margin-top: 0;">Project Details:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Scope:</strong> {scope_summary}</p>
                    </div>

                    <p>{urgency_text}</p>
                    
                    {deadline_context}

                    <p>This homeowner is pre-qualified and ready to hire the right contractor. <strong>Would you be interested in submitting a competitive bid?</strong></p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #4caf50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Full Project Details</a>
                    </div>

                    <p>Best regards,<br>
                    The Instabids Team<br>
                    <em>Connecting quality contractors with ready-to-hire homeowners</em></p>

                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                    <p style="font-size: 12px; color: #666;">
                        This project was matched to you based on your specialties and service area.
                        If you're not interested, simply ignore this email.
                    </p>
                </body>
                </html>
                """,
                "plain_body": """
Hi {contractor_name},

{urgency_prefix}Kitchen Remodel Opportunity in {location}

We have an {urgency_level} kitchen remodeling project that matches your expertise.

Project Details:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Scope: {scope_summary}

{urgency_text}

{deadline_context}

This homeowner is pre-qualified and ready to hire. Would you be interested in submitting a bid?

View full project details: {bid_card_link}

Best regards,
The Instabids Team
Connecting quality contractors with ready-to-hire homeowners
                """
            },
            "kitchen_standard_email": {
                "subject": "{deadline_urgency_modifier}Kitchen Remodel Project in {location} - ${budget_min}-${budget_max}",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #2196f3;">New Kitchen Remodel Opportunity</h2>

                    <p>Hello {contractor_name},</p>

                    <p>I hope this email finds you well! We have a kitchen remodeling project in <strong>{location}</strong> that would be perfect for {company_name}.</p>

                    <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border: 1px solid #dee2e6;">
                        <h3 style="margin-top: 0; color: #495057;">Project Overview:</h3>
                        <ul style="margin-bottom: 0;">
                            <li><strong>Project Type:</strong> {project_type}</li>
                            <li><strong>Budget Range:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                    </div>

                    <p><strong>Project Description:</strong><br>
                    {scope_summary}</p>

                    {deadline_context}

                    <p>The homeowner has already completed their project planning and is ready to review competitive bids from qualified contractors like yourself.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">View Complete Project Details</a>
                    </div>

                    <p>If this project interests you, please review the full details and submit your bid. We look forward to potentially working together!</p>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
Hello {contractor_name},

New Kitchen Remodel Opportunity in {location}

We have a kitchen remodeling project that would be perfect for {company_name}.

Project Overview:
- Project Type: {project_type}
- Budget Range: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}

Project Description:
{scope_summary}

{deadline_context}

The homeowner is ready to review competitive bids from qualified contractors.

View complete project details: {bid_card_link}

If this project interests you, please review the details and submit your bid.

Best regards,
The Instabids Team
                """
            },
            "bathroom_standard_email": {
                "subject": "{deadline_urgency_modifier}Bathroom Renovation Project - {location} - ${budget_min}-${budget_max}",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #673ab7;">Bathroom Renovation Opportunity</h2>

                    <p>Hello {contractor_name},</p>

                    <p>We have a bathroom renovation project in <strong>{location}</strong> that matches your expertise perfectly.</p>

                    <div style="background: #f3e5f5; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #673ab7;">
                        <h3 style="margin-top: 0;">Project Details:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Scope:</strong> {scope_summary}</p>
                    </div>

                    <p>This is an excellent opportunity for a skilled contractor to work on a quality bathroom renovation project.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #673ab7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Project Details</a>
                    </div>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
Hello {contractor_name},

Bathroom Renovation Opportunity in {location}

Project Details:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Scope: {scope_summary}

View project details: {bid_card_link}

Best regards,
The Instabids Team
                """
            },
            "mold_urgent_email": {
                "subject": "{urgency_prefix}Mold Remediation - {location} - ${budget_min}-${budget_max} - Immediate Response Needed",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #d32f2f;">{urgency_prefix}Emergency Mold Remediation Needed</h2>

                    <p>Hi {contractor_name},</p>

                    <p>We have an <strong>URGENT mold remediation emergency</strong> in <strong>{location}</strong> that requires certified professionals immediately.</p>

                    <div style="background: #ffebee; padding: 15px; margin: 20px 0; border-left: 4px solid #d32f2f;">
                        <h3 style="margin-top: 0; color: #d32f2f;">URGENT Project Details:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Situation:</strong> {scope_summary}</p>
                        <p style="color: #d32f2f; font-weight: bold;">This is a health emergency requiring EPA-certified professionals.</p>
                    </div>

                    <p>{urgency_text}</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #d32f2f; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">RESPOND NOW - View Emergency Details</a>
                    </div>

                    <p style="font-weight: bold;">Please respond immediately if you can help with this emergency.</p>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
{urgency_prefix}EMERGENCY MOLD REMEDIATION - {location}

Hi {contractor_name},

We have an URGENT mold remediation emergency that requires certified professionals immediately.

URGENT Project Details:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Situation: {scope_summary}

This is a health emergency requiring EPA-certified professionals.

{urgency_text}

View emergency details: {bid_card_link}

Please respond immediately if you can help.

Best regards,
The Instabids Team
                """
            },
            "mold_standard_email": {
                "subject": "Mold Remediation Project - {location} - ${budget_min}-${budget_max}",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #4caf50;">Mold Remediation Project Opportunity</h2>

                    <p>Hello {contractor_name},</p>

                    <p>We have a mold remediation project in <strong>{location}</strong> that matches your expertise and certifications.</p>

                    <div style="background: #f1f8e9; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #4caf50;">
                        <h3 style="margin-top: 0;">Project Details:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Scope:</strong> {scope_summary}</p>
                    </div>

                    <p>This project requires EPA-certified mold remediation professionals with proper equipment and protocols.</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #4caf50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Full Project Details</a>
                    </div>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
Hello {contractor_name},

Mold Remediation Project in {location}

Project Details:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Scope: {scope_summary}

This project requires EPA-certified mold remediation professionals.

View full details: {bid_card_link}

Best regards,
The Instabids Team
                """
            },
            "general_urgent_email": {
                "subject": "{urgency_prefix}{project_type} - {location} - ${budget_min}-${budget_max} - Immediate Response Needed",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #d32f2f;">{urgency_prefix}Urgent Project Opportunity</h2>

                    <p>Hi {contractor_name},</p>

                    <p>We have an <strong>URGENT {project_type}</strong> project in <strong>{location}</strong> that needs immediate attention.</p>

                    <div style="background: #ffebee; padding: 15px; margin: 20px 0; border-left: 4px solid #d32f2f;">
                        <h3 style="margin-top: 0; color: #d32f2f;">URGENT Project Details:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Details:</strong> {scope_summary}</p>
                    </div>

                    <p>{urgency_text}</p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #d32f2f; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 18px;">RESPOND NOW</a>
                    </div>

                    <p style="font-weight: bold;">Time is critical - please respond as soon as possible.</p>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
{urgency_prefix}URGENT PROJECT - {location}

Hi {contractor_name},

We have an URGENT {project_type} project that needs immediate attention.

URGENT Project Details:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Details: {scope_summary}

{urgency_text}

View details now: {bid_card_link}

Time is critical - please respond ASAP.

Best regards,
The Instabids Team
                """
            },
            "general_standard_email": {
                "subject": "New Project Opportunity - {project_type} in {location}",
                "html_body": """
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #4caf50;">New Project Opportunity</h2>

                    <p>Hello {contractor_name},</p>

                    <p>We have a {project_type} project in <strong>{location}</strong> that we believe would be a great fit for your skills.</p>

                    <div style="background: #f1f8e9; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #4caf50;">
                        <h3 style="margin-top: 0;">Project Information:</h3>
                        <ul>
                            <li><strong>Type:</strong> {project_type}</li>
                            <li><strong>Budget:</strong> ${budget_min} - ${budget_max}</li>
                            <li><strong>Timeline:</strong> {timeline}</li>
                            <li><strong>Location:</strong> {location}</li>
                        </ul>
                        <p><strong>Details:</strong> {scope_summary}</p>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{bid_card_link}" style="background: #4caf50; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;">View Full Details</a>
                    </div>

                    <p>Best regards,<br>
                    The Instabids Team</p>
                </body>
                </html>
                """,
                "plain_body": """
Hello {contractor_name},

New Project Opportunity: {project_type} in {location}

Project Information:
- Type: {project_type}
- Budget: ${budget_min} - ${budget_max}
- Timeline: {timeline}
- Location: {location}
- Details: {scope_summary}

View full details: {bid_card_link}

Best regards,
The Instabids Team
                """
            }
        }

    def _load_sms_templates(self) -> dict[str, dict[str, str]]:
        """Load SMS templates for different scenarios"""
        return {
            "urgent_sms": {
                "content": "{urgency_prefix}{project_type} in {location}. ${budget_min}-${budget_max}. URGENT. Reply YES for details. -Instabids"
            },
            "kitchen_sms": {
                "content": "Kitchen remodel in {location}. ${budget_min}-${budget_max}. Perfect for your skills. Reply YES for project details. -Instabids"
            },
            "bathroom_sms": {
                "content": "Bathroom renovation in {location}. ${budget_min}-${budget_max}. Great opportunity. Reply YES to learn more. -Instabids"
            },
            "roofing_sms": {
                "content": "Roofing project in {location}. ${budget_min}-${budget_max}. {timeline}. Reply YES for details. -Instabids"
            },
            "general_sms": {
                "content": "{project_type} project in {location}. ${budget_min}-${budget_max}. Interested? Reply YES for info. -Instabids"
            }
        }
