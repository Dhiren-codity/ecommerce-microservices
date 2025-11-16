require 'rails_helper'
require 'spec_helper'

RSpec.describe Router do
  let(:router) do
    Router.new
  end

  describe '#route' do
    context 'when path matches auth service' do
      let(:path) do
        '/api/auth/login'
      end

      it 'returns the auth service URL and caches the result' do
        first = router.route(path)
        second = router.route(path)
        expect(first).to eq('http://localhost:8080')
        expect(second).to eq('http://localhost:8080')
        expect(router.instance_variable_get(:@route_cache)[path]).to eq('http://localhost:8080')
      end
    end

    context 'when path matches analytics service' do
      let(:path) do
        '/api/analytics/activity'
      end

      it 'returns the analytics service URL and caches the result' do
        first = router.route(path)
        second = router.route(path)
        expect(first).to eq('http://localhost:8000')
        expect(second).to eq('http://localhost:8000')
        expect(router.instance_variable_get(:@route_cache)[path]).to eq('http://localhost:8000')
      end
    end

    context 'when path matches products service' do
      let(:path) do
        '/api/products/123'
      end

      it 'returns the products service URL and caches the result' do
        first = router.route(path)
        second = router.route(path)
        expect(first).to eq('http://localhost:9000')
        expect(second).to eq('http://localhost:9000')
        expect(router.instance_variable_get(:@route_cache)[path]).to eq('http://localhost:9000')
      end
    end

    context 'when path does not match any service' do
      let(:path) do
        '/api/unknown'
      end

      it 'returns nil and caches nil for the path' do
        first = router.route(path)
        second = router.route(path)
        expect(first).to be_nil
        expect(second).to be_nil
        expect(router.instance_variable_get(:@route_cache).key?(path)).to be true
      end
    end

    it 'calls determine_service only once for the same path due to caching' do
      allow(router).to receive(:determine_service).and_call_original
      path = '/api/products/1'
      router.route(path)
      router.route(path)
      expect(router).to have_received(:determine_service).once
    end

    it 'calls determine_service for each unique path' do
      allow(router).to receive(:determine_service).and_call_original
      router.route('/api/products/1')
      router.route('/api/products/2')
      expect(router).to have_received(:determine_service).twice
    end
  end

  describe '#determine_service' do
    it 'returns auth service for /api/auth paths' do
      expect(router.determine_service('/api/auth/login')).to eq('http://localhost:8080')
    end

    it 'returns analytics service for /api/analytics paths' do
      expect(router.determine_service('/api/analytics/events')).to eq('http://localhost:8000')
    end

    it 'returns products service for /api/products paths' do
      expect(router.determine_service('/api/products/123')).to eq('http://localhost:9000')
    end

    it 'returns nil for non-matching paths' do
      expect(router.determine_service('/api/other')).to be_nil
      expect(router.determine_service('/health')).to be_nil
    end
  end

  describe '#build_url' do
    it 'returns nil when service_url is nil' do
      expect(router.build_url(nil, '/api/auth/login')).to be_nil
    end

    it 'joins service_url and path' do
      url = router.build_url('http://localhost:8080', '/api/auth/login')
      expect(url).to eq('http://localhost:8080/api/auth/login')
    end

    it 'preserves the full path including query string' do
      url = router.build_url('http://localhost:8000', '/api/analytics/events?foo=bar')
      expect(url).to eq('http://localhost:8000/api/analytics/events?foo=bar')
    end
  end

  describe '#validate_path' do
    it 'returns false for nil' do
      expect(router.validate_path(nil)).to be false
    end

    it 'returns false for empty' do
      expect(router.validate_path('')).to be false
    end

    it 'returns false for non /api/ prefixed path' do
      expect(router.validate_path('/v1/users')).to be false
    end

    it 'returns true for valid /api/ path' do
      expect(router.validate_path('/api/users')).to be true
    end
  end

  describe '#clear_cache' do
    it 'clears the internal route cache' do
      path = '/api/products/1'
      router.route(path)
      expect(router.instance_variable_get(:@route_cache).key?(path)).to be true
      router.clear_cache
      expect(router.instance_variable_get(:@route_cache).key?(path)).to be false
    end

    it 'forces re-computation after cache clear' do
      path = '/api/auth/login'
      allow(router).to receive(:determine_service).and_call_original
      router.route(path)
      router.clear_cache
      router.route(path)
      expect(router).to have_received(:determine_service).twice
    end
  end

  describe '#is_activity_endpoint?' do
    it 'returns true for /api/analytics/activity' do
      expect(router.is_activity_endpoint?('/api/analytics/activity')).to be true
    end

    it 'returns true for /api/auth/activity' do
      expect(router.is_activity_endpoint?('/api/auth/activity')).to be true
    end

    it 'returns true for /api/users/:id/activity' do
      expect(router.is_activity_endpoint?('/api/users/123/activity')).to be true
    end

    it 'returns false for unrelated paths' do
      expect(router.is_activity_endpoint?('/api/auth/login')).to be false
    end

    it 'returns false for nil or empty' do
      expect(router.is_activity_endpoint?(nil)).to be false
      expect(router.is_activity_endpoint?('')).to be false
    end
  end

  describe '#extract_user_id' do
    it 'extracts alphanumeric and hyphen ids' do
      expect(router.extract_user_id('/api/users/abc-123/activity')).to eq('abc-123')
      expect(router.extract_user_id('/api/users/ZZZ999/activity')).to eq('ZZZ999')
    end

    it 'returns nil when id contains underscore (not matched by regex)' do
      expect(router.extract_user_id('/api/users/XYZ_123/activity')).to be_nil
    end

    it 'returns nil when path does not contain a user segment' do
      expect(router.extract_user_id('/api/analytics/activity')).to be_nil
    end

    it 'returns nil for nil or empty path' do
      expect(router.extract_user_id(nil)).to be_nil
      expect(router.extract_user_id('')).to be_nil
    end
  end

  describe '#get_activity_service' do
    it 'returns nil for non-activity paths' do
      expect(router.get_activity_service('/api/auth/login')).to be_nil
    end

    it 'routes auth activity to auth service' do
      expect(router.get_activity_service('/api/auth/activity')).to eq('http://localhost:8080')
    end

    it 'routes analytics activity to analytics service' do
      expect(router.get_activity_service('/api/analytics/activity')).to eq('http://localhost:8000')
    end

    it 'routes user activity to analytics service by default' do
      expect(router.get_activity_service('/api/users/123/activity')).to eq('http://localhost:8000')
    end
  end

  describe '#route_with_priority' do
    it 'returns nil when no service is found' do
      result = router.route_with_priority('/api/unknown')
      expect(result).to be_nil
    end

    it 'returns a routing hash with normal priority by default' do
      fixed_time = Time.at(1_700_000_000)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/products/42'
      result = router.route_with_priority(path)
      expect(result[:service]).to eq('http://localhost:9000')
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('normal')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'returns a routing hash with high priority when is_critical is true' do
      fixed_time = Time.at(1_700_000_001)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/auth/login'
      result = router.route_with_priority(path, true)
      expect(result[:service]).to eq('http://localhost:8080')
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('high')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'uses cached route when available' do
      path = '/api/analytics/activity'
      allow(router).to receive(:determine_service).and_call_original
      router.route(path)
      router.route_with_priority(path)
      expect(router).to have_received(:determine_service).once
    end
  end
end
