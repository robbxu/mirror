def get_belief_analysis_schema():
    ## flattened version of original 
    schema = {
        "topics": {
            "description": "How beliefs manifest in specific topic areas",
            "topics": [
                {
                    "topic": "string - The specific subject area being analyzed",
                    "beliefs": [
                        {
                            "belief": "string - A core belief that influences this topic",
                            "type": "string - Either an emotional reflection, a key opinion, or a core belief",
                        }
                    ],
                }
            ]
        },
    }
    
    return schema

def get_style_analysis_schema():
    ## flattened linguistic fingerprint schema
    schema = {
        "linguistic_patterns": {
            "description": "Core characteristics of the subject's writing style",
            
            "sentence_characteristics": {
                "description": "Patterns in sentence construction and usage",
                
                "length_patterns": {
                    "short": "string - Frequency and usage of brief, concise sentences (rare|occasional|common|very_common)",
                    "medium": "string - Frequency and usage of moderate-length sentences (rare|occasional|common|very_common)",
                    "long": "string - Frequency and usage of extended, complex sentences (rare|occasional|common|very_common)",
                    "impact": "string - How sentence length affects the writing's impact (e.g., punchy, flowing, detailed)"
                },
                
                "structure_preferences": {
                    "simple": "string - Use of straightforward subject-verb-object sentences (rare|occasional|common|very_common)",
                    "compound": "string - Use of multiple independent clauses (rare|occasional|common|very_common)",
                    "complex": "string - Use of dependent and independent clauses (rare|occasional|common|very_common)",
                    "contexts": ["string - When certain sentence structures are typically employed"]
                },
                
                "rhythm_elements": {
                    "punctuation_style": {
                        "comma_usage": "string - Frequency of comma use (sparse|moderate|heavy)",
                        "semicolon_usage": "string - Frequency of semicolon use (sparse|moderate|heavy)",
                        "dash_usage": "string - Frequency of dash use (sparse|moderate|heavy)"
                    },
                    "flow_patterns": ["string - Characteristic sentence transitions and emphasis techniques"]
                }
            },
            
            "paragraph_style": {
                "description": "How paragraphs are constructed and developed",
                
                "length": "string - Typical paragraph length (brief|moderate|extensive)",
                "development": "string - How ideas progress within paragraphs (linear|circular|branching)",
                "pacing": "string - Speed at which ideas are presented (rapid|measured|gradual)",
                "construction_patterns": ["string - Characteristic ways of opening, developing and closing paragraphs"]
            },
            
            "vocabulary_patterns": {
                "description": "Word choice preferences and patterns",
                
                "distinctive_words": ["string - Characteristic adjectives, verbs, and intensifiers frequently used"],
                "signature_phrases": ["string - Repeated expressions, metaphor types, and idiom usage"],
                "register_variations": ["string - Shifts between formal and casual language and their triggers"]
            },
            
            "expression_patterns": {
                "description": "Rhetorical approaches and tone variations",
                
                "rhetorical_preferences": ["string - Favorite devices and argument structures"],
                "humor_style": ["string - Types of humor used and their delivery"],
                "emotional_expression": ["string - How emotions are conveyed in writing"]
            }
        },
        
        "contextual_shifts": {
            "description": "How writing style changes across different emotional states and topics",
            
            "emotional_variations": {
                "description": "Style shifts based on emotional state",
                
                "in_anger": {
                    "sentence_style": "string - How sentences change when expressing anger (shorter|choppier|more_complex)",
                    "word_choices": ["string - Characteristic word choices when angry"],
                    "rhythm_changes": ["string - How writing rhythm and flow change when angry"]
                },
                
                "in_excitement": {
                    "sentence_style": "string - How sentences change when excited (faster|more_flowing|more_fragmented)",
                    "word_choices": ["string - Characteristic word choices when excited"],
                    "rhythm_changes": ["string - How writing rhythm and flow change when excited"]
                },
                
                "in_reflection": {
                    "sentence_style": "string - How sentences change when reflective (longer|more_complex|more_measured)",
                    "word_choices": ["string - Characteristic word choices when reflective"],
                    "rhythm_changes": ["string - How writing rhythm and flow change when reflective"]
                }
            },
            
            "topic_adaptations": {
                "description": "Style shifts based on subject matter",
                
                "technical_topics": {
                    "complexity": "string - How complexity changes for technical subjects (simpler|unchanged|more_complex)",
                    "vocabulary_shifts": ["string - How vocabulary changes for technical topics"],
                    "structure_changes": ["string - How structure changes for technical topics"]
                },
                
                "personal_topics": {
                    "complexity": "string - How complexity changes for personal subjects (simpler|unchanged|more_complex)",
                    "vocabulary_shifts": ["string - How vocabulary changes for personal topics"],
                    "structure_changes": ["string - How structure changes for personal topics"]
                },
                
                "abstract_topics": {
                    "complexity": "string - How complexity changes for abstract subjects (simpler|unchanged|more_complex)",
                    "vocabulary_shifts": ["string - How vocabulary changes for abstract topics"],
                    "structure_changes": ["string - How structure changes for abstract topics"]
                }
            }
        }
    }
    return schema