require 'rails_helper'
require 'spec_helper'

RSpec.describe Router do
  let(:router) do
    Router.new
  end

  describe '#determine_service' do
    it 'routes /api/auth to auth service' do
      service = router.determine_service('/api/auth/login')
      expect(service).to eq('http://localhost:8080')
    end

    it 'routes /api/analytics to analytics service' do
      service = router.determine_service('/api/analytics/activity')
      expect(service).to eq('http://localhost:8000')
    end

    it 'routes /api/products to products service' do
      service = router.determine_service('/api/products/123')
      expect(service).to eq('http://localhost:9000')
    end

    it 'returns nil for unknown paths' do
      service = router.determine_service('/unknown/path')
      expect(service).to be_nil
    end
  end

  describe '#route' do
    it 'returns the service url for a known path' do
      result = router.route('/api/auth/login')
      expect(result).to eq('http://localhost:8080')
    end

    it 'returns nil for an unknown path' do
      result = router.route('/not/api/path')
      expect(result).to be_nil
    end

    it 'caches the routing result for subsequent calls (known path)' do
      path = '/api/products/list'
      expect(router).to receive(:determine_service).once.and_call_original
      first = router.route(path)
      second = router.route(path)
      expect(second).to eq(first)
      expect(second).to eq('http://localhost:9000')
    end

    it 'caches nil result for unknown paths and does not re-calculate' do
      path = '/no/match/here'
      expect(router).to receive(:determine_service).once.and_call_original
      first = router.route(path)
      second = router.route(path)
      expect(first).to be_nil
      expect(second).to be_nil
    end
  end

  describe '#build_url' do
    it 'concatenates service url and path' do
      url = router.build_url('http://localhost:8080', '/api/auth/login')
      expect(url).to eq('http://localhost:8080/api/auth/login')
    end

    it 'returns nil when service url is nil' do
      url = router.build_url(nil, '/api/auth/login')
      expect(url).to be_nil
    end

    it 'handles empty path by concatenation behavior' do
      url = router.build_url('http://localhost:9000', '')
      expect(url).to eq('http://localhost:9000')
    end
  end

  describe '#validate_path' do
    it 'returns true for a valid api path' do
      expect(router.validate_path('/api/auth/login')).to be true
    end

    it 'returns false for nil' do
      expect(router.validate_path(nil)).to be false
    end

    it 'returns false for empty string' do
      expect(router.validate_path('')).to be false
    end

    it 'returns false for path not starting with /api/' do
      expect(router.validate_path('/foo/bar')).to be false
    end

    it 'returns false for path missing leading slash' do
      expect(router.validate_path('api/auth')).to be false
    end
  end

  describe '#clear_cache' do
    it 'clears the route cache so subsequent calls re-calculate' do
      path = '/api/auth/login'
      first = router.route(path)
      expect(first).to eq('http://localhost:8080')

      router.clear_cache

      expect(router).to receive(:determine_service).once.and_call_original
      second = router.route(path)
      expect(second).to eq('http://localhost:8080')
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
      expect(router.is_activity_endpoint?('/api/users/abc-123/activity')).to be true
    end

    it 'returns false for non-activity analytics path' do
      expect(router.is_activity_endpoint?('/api/analytics/events')).to be false
    end

    it 'returns false for nil' do
      expect(router.is_activity_endpoint?(nil)).to be false
    end

    it 'returns false for empty string' do
      expect(router.is_activity_endpoint?('')).to be false
    end
  end

  describe '#extract_user_id' do
    it 'extracts alphanumeric-dash user id' do
      id = router.extract_user_id('/api/users/aB-123-x/activity')
      expect(id).to eq('aB-123-x')
    end

    it 'extracts user id when users appears mid-path' do
      id = router.extract_user_id('/foo/bar/users/xyz-9/profile')
      expect(id).to eq('xyz-9')
    end

    it 'returns nil when no user id segment present' do
      id = router.extract_user_id('/api/auth/login')
      expect(id).to be_nil
    end

    it 'returns nil for nil' do
      id = router.extract_user_id(nil)
      expect(id).to be_nil
    end

    it 'returns nil for empty string' do
      id = router.extract_user_id('')
      expect(id).to be_nil
    end
  end

  describe '#get_activity_service' do
    it 'returns auth service for auth activity path' do
      service = router.get_activity_service('/api/auth/activity')
      expect(service).to eq('http://localhost:8080')
    end

    it 'returns analytics service for analytics activity path' do
      service = router.get_activity_service('/api/analytics/activity')
      expect(service).to eq('http://localhost:8000')
    end

    it 'returns analytics service for user activity path by default' do
      service = router.get_activity_service('/api/users/xyz/activity')
      expect(service).to eq('http://localhost:8000')
    end

    it 'returns nil for non-activity paths' do
      service = router.get_activity_service('/api/products/123')
      expect(service).to be_nil
    end
  end

  describe '#route_with_priority' do
    it 'returns routing metadata with normal priority' do
      fixed_time = Time.utc(2023, 1, 1, 12, 0, 0)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/products/123'
      result = router.route_with_priority(path, false)
      expect(result[:service]).to eq('http://localhost:9000')
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('normal')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'returns routing metadata with high priority' do
      fixed_time = Time.utc(2024, 6, 1, 10, 30, 0)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/auth/login'
      result = router.route_with_priority(path, true)
      expect(result[:service]).to eq('http://localhost:8080')
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('high')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'returns nil when service cannot be determined' do
      result = router.route_with_priority('/unknown/path', true)
      expect(result).to be_nil
    end
  end
end
