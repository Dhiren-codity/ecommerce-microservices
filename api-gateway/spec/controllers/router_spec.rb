require 'rails_helper'
require 'spec_helper'

RSpec.describe Router do
  let(:router) do
    Router.new
  end

  describe '.new' do
    it 'initializes with an empty route cache' do
      expect(router.instance_variable_get(:@route_cache)).to eq({})
    end
  end

  describe '#determine_service' do
    it 'returns auth service for /api/auth paths' do
      expect(router.determine_service('/api/auth/login')).to eq(Router::SERVICES[:auth])
    end

    it 'returns analytics service for /api/analytics paths' do
      expect(router.determine_service('/api/analytics/activity')).to eq(Router::SERVICES[:analytics])
    end

    it 'returns products service for /api/products paths' do
      expect(router.determine_service('/api/products/42')).to eq(Router::SERVICES[:products])
    end

    it 'returns nil for unknown paths' do
      expect(router.determine_service('/unknown')).to be_nil
    end
  end

  describe '#route' do
    it 'routes auth path to auth service' do
      path = '/api/auth/login'
      expect(router.route(path)).to eq(Router::SERVICES[:auth])
    end

    it 'routes analytics path to analytics service' do
      path = '/api/analytics/activity'
      expect(router.route(path)).to eq(Router::SERVICES[:analytics])
    end

    it 'routes products path to products service' do
      path = '/api/products/123'
      expect(router.route(path)).to eq(Router::SERVICES[:products])
    end

    it 'returns nil for unmatched path' do
      path = '/api/unknown/route'
      expect(router.route(path)).to be_nil
    end

    it 'caches the routing decision' do
      path = '/api/products/555'
      expect(router.route(path)).to eq(Router::SERVICES[:products])
      expect(router.instance_variable_get(:@route_cache)[path]).to eq(Router::SERVICES[:products])
    end

    it 'uses the cache on subsequent calls' do
      path = '/api/products/777'
      expect(router).to receive(:determine_service).once.and_call_original
      router.route(path)
      router.route(path)
    end

    it 'caches nil decisions as well' do
      path = '/unknown'
      expect(router.route(path)).to be_nil
      expect(router.instance_variable_get(:@route_cache)).to have_key(path)
      expect(router.route(path)).to be_nil
    end
  end

  describe '#build_url' do
    it 'returns nil when service_url is nil' do
      expect(router.build_url(nil, '/api/auth/login')).to be_nil
    end

    it 'concatenates service_url and path' do
      service_url = Router::SERVICES[:auth]
      path = '/api/auth/login'
      expect(router.build_url(service_url, path)).to eq("#{service_url}#{path}")
    end
  end

  describe '#validate_path' do
    it 'returns false when path is nil' do
      expect(router.validate_path(nil)).to eq(false)
    end

    it 'returns false when path is empty' do
      expect(router.validate_path('')).to eq(false)
    end

    it "returns false when path doesn't start with /api/" do
      expect(router.validate_path('/v1/users')).to eq(false)
    end

    it 'returns true for a valid /api/ path' do
      expect(router.validate_path('/api/products/1')).to eq(true)
    end
  end

  describe '#clear_cache' do
    it 'clears the route cache' do
      path = '/api/auth/login'
      router.route(path)
      expect(router.instance_variable_get(:@route_cache)).not_to be_empty
      router.clear_cache
      expect(router.instance_variable_get(:@route_cache)).to be_empty
    end

    it 'forces recomputation after clearing cache' do
      path = '/api/products/42'
      router.route(path)
      router.clear_cache
      expect(router).to receive(:determine_service).once.and_call_original
      router.route(path)
    end
  end

  describe '#is_activity_endpoint?' do
    it 'returns true for /api/analytics/activity' do
      expect(router.is_activity_endpoint?('/api/analytics/activity')).to eq(true)
    end

    it 'returns true for /api/auth/activity' do
      expect(router.is_activity_endpoint?('/api/auth/activity')).to eq(true)
    end

    it 'returns true for /api/users/:id/activity' do
      expect(router.is_activity_endpoint?('/api/users/abc-123/activity')).to eq(true)
    end

    it 'returns false for non-activity endpoints' do
      expect(router.is_activity_endpoint?('/api/products/1')).to eq(false)
    end

    it 'returns false for nil or empty path' do
      expect(router.is_activity_endpoint?(nil)).to eq(false)
      expect(router.is_activity_endpoint?('')).to eq(false)
    end
  end

  describe '#extract_user_id' do
    it 'extracts alphanumeric user id with dashes' do
      path = '/api/users/user-123-abc/activity'
      expect(router.extract_user_id(path)).to eq('user-123-abc')
    end

    it 'returns nil if no user id in path' do
      path = '/api/products/12'
      expect(router.extract_user_id(path)).to be_nil
    end

    it 'returns nil for nil or empty path' do
      expect(router.extract_user_id(nil)).to be_nil
      expect(router.extract_user_id('')).to be_nil
    end
  end

  describe '#get_activity_service' do
    it 'returns auth service for auth activity endpoints' do
      path = '/api/auth/activity'
      expect(router.get_activity_service(path)).to eq(Router::SERVICES[:auth])
    end

    it 'returns analytics service for analytics activity endpoints' do
      path = '/api/analytics/activity'
      expect(router.get_activity_service(path)).to eq(Router::SERVICES[:analytics])
    end

    it 'returns analytics service for users activity endpoints by default' do
      path = '/api/users/123/activity'
      expect(router.get_activity_service(path)).to eq(Router::SERVICES[:analytics])
    end

    it 'returns nil when not an activity endpoint' do
      path = '/api/products/1'
      expect(router.get_activity_service(path)).to be_nil
    end
  end

  describe '#route_with_priority' do
    it 'returns a routing hash with normal priority by default' do
      fixed_time = Time.at(1_700_000_000)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/products/1'
      result = router.route_with_priority(path)
      expect(result[:service]).to eq(Router::SERVICES[:products])
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('normal')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'returns high priority when is_critical is true' do
      fixed_time = Time.at(1_700_000_100)
      allow(Time).to receive(:now).and_return(fixed_time)
      path = '/api/auth/login'
      result = router.route_with_priority(path, true)
      expect(result[:service]).to eq(Router::SERVICES[:auth])
      expect(result[:path]).to eq(path)
      expect(result[:priority]).to eq('high')
      expect(result[:timestamp]).to eq(fixed_time)
    end

    it 'returns nil when the path cannot be routed' do
      path = '/unknown'
      expect(router.route_with_priority(path)).to be_nil
    end

    it 'respects cache during priority routing' do
      path = '/api/analytics/activity'
      router.route(path)
      expect(router).not_to receive(:determine_service)
      result = router.route_with_priority(path)
      expect(result[:service]).to eq(Router::SERVICES[:analytics])
    end
  end
end
