class ContentDecisionEngine:
    def __init__(self, rule_manager, content_repository):
        self.rule_manager = rule_manager
        self.content_repository = content_repository
        self.recent_selections = []
    
    def calculate_rule_match(self, rule, current_conditions):
        """Calculate how well current conditions match a rule"""
        score = 0
        max_score = 0
        
        # Check environmental matches
        if "environmental" in rule["conditions"]:
            for factor, condition in rule["conditions"]["environmental"].items():
                if factor in current_conditions["environmental"]:
                    current_value = current_conditions["environmental"][factor]
                    max_score += 1
                    
                    # Handle range conditions
                    if isinstance(condition, dict) and "min" in condition and "max" in condition:
                        if condition["min"] <= current_value <= condition["max"]:
                            score += 1
                    
                    # Handle list conditions
                    elif isinstance(condition, list) and current_value in condition:
                        score += 1
        
        # Check audience matches
        if "audience" in rule["conditions"]:
            for factor, condition in rule["conditions"]["audience"].items():
                if factor in current_conditions["audience"]:
                    current_value = current_conditions["audience"][factor]
                    max_score += 1
                    
                    # Handle list conditions (for age groups, etc.)
                    if isinstance(condition, list) and current_value in condition:
                        score += 1
        
        # Check temporal matches
        if "temporal" in rule["conditions"]:
            for factor, condition in rule["conditions"]["temporal"].items():
                if factor in current_conditions["temporal"]:
                    current_value = current_conditions["temporal"][factor]
                    max_score += 1
                    
                    if isinstance(condition, list) and current_value in condition:
                        score += 1
        
        # Calculate percentage match
        match_percentage = score / max_score if max_score > 0 else 0
        final_score = match_percentage * rule["weight"] * rule["priority"]
        
        return final_score
    
    def get_content_selection(self, environmental_data, audience_data, time_data):
        """Determine which content to display based on current conditions"""
        current_conditions = {
            "environmental": environmental_data,
            "audience": audience_data,
            "temporal": time_data
        }
        
        # Get all rules
        rules = self.rule_manager.get_rules()
        
        # Calculate scores for all rules
        scored_content = []
        for rule in rules:
            score = self.calculate_rule_match(rule, current_conditions)
            if score > 0:  # Only consider non-zero matches
                scored_content.append({
                    "content_id": rule["content_id"],
                    "score": score,
                    "rule_id": rule["id"]
                })
        
        # Sort by score (highest first)
        scored_content.sort(key=lambda x: x["score"], reverse=True)
        
        # Avoid repetition by checking recent selections
        for item in scored_content[:3]:  # Consider top 3 candidates
            if item["content_id"] not in [recent["content_id"] for recent in self.recent_selections[-2:]]:
                # Update recent selections (limit to last 5)
                self.recent_selections.append(item)
                if len(self.recent_selections) > 5:
                    self.recent_selections.pop(0)
                return item
        
        # If all top options were recently shown, pick the highest scored one anyway
        if scored_content:
            selected = scored_content[0]
            self.recent_selections.append(selected)
            if len(self.recent_selections) > 5:
                self.recent_selections.pop(0)
            return selected
            
        return None  # No suitable content found