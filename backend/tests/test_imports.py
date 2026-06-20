def test_routing_service_imports_without_side_effect_path_setup():
    import backend.data.routing_service as routing_service

    assert routing_service.routing_service is not None
