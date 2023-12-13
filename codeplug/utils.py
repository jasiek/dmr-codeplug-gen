class TypeChecked:
    def __init__(self, name, expected_type):
        self.name = name
        self.expected_type = expected_type

    def __get__(self, instance, owner):
        return instance.__dict__.get(self.name, None)

    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(f"Expected {self.expected_type}, got {type(value)}")
        instance.__dict__[self.name] = value

def create_class_with_attributes(attribute_dict):
    class CustomClass:
        def __init__(self):
            for name, type_ in attribute_dict.items():
                setattr(self, name, None)  # Initialize all attributes to None

    for name, type_ in attribute_dict.items():
        setattr(CustomClass, name, TypeChecked(name, type_))

    return CustomClass
