from uuid import uuid4

from citrine._rest.resource import ResourceRef


def test_module_ref_serialization():
    # Given
    m_uid = uuid4()
    ref = ResourceRef(uid=m_uid)

    # When
    ref_data = ref.dump()

    # Then
    assert ref_data['module_uid'] == str(m_uid)
