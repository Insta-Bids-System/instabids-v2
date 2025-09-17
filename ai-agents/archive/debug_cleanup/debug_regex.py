import re

user_input = "hi, i'm from turf grass artificial solutions. we're a landscaping company based in south florida."

patterns = [
    r"i'm\s+(?!from\s)([^.,!]+?)\s*[.,!]",  # "I'm StateDebug Plumbing." but NOT "I'm from..."
    r"i'm\s+(\w+)\s+from\s+([^.,]+)",  # "I'm John from HVAC Solutions"
    r"(?:i'm\s+)from\s+([^.,]+)",  # "I'm from HVAC Solutions"
    r"company\s+is\s+([^.,]+)",  # "company is HVAC Solutions"
    r"business\s+is\s+([^.,]+)",  # "business is HVAC Solutions"
    r"i\s+own\s+([^.,]+)",  # "I own HVAC Solutions"
    r"we're\s+([^.,]+)",  # "We're HVAC Solutions"
    r"my\s+company\s+is\s+([^.,]+)",  # "my company is HVAC Solutions"
    r"account\s+(?:for\s+)?([^.,\s]+(?:\s+[^.,\s]+)*)",  # "create account for ABC Company"
]

print(f"Testing: {user_input}")
print()

for i, pattern in enumerate(patterns):
    match = re.search(pattern, user_input)
    if match:
        groups = match.groups()
        print(f"Pattern {i} MATCHED: {pattern}")
        print(f"  Full match: '{match.group()}'")
        print(f"  Groups: {groups}")
        
        if i == 0:
            potential_company = groups[0].strip()
        else:
            potential_company = groups[-1].strip()
        
        print(f"  Extracted: '{potential_company}'")
        print()
        break
    else:
        print(f"Pattern {i} no match: {pattern}")