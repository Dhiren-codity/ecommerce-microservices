require 'sinatra/base'
require_relative 'controllers/router'
require_relative 'controllers/rate_limiter'
require_relative 'models/request_logger'

class Gateway < Sinatra::Base
  configure do
    set :router, Router.new
    set :rate_limiter, RateLimiter.new(100, 60)
    set :logger, RequestLogger.new
  end

  before do
    content_type :json

    client_id = request.ip
    unless settings.rate_limiter.allow?(client_id)
      halt 429, { error: 'Rate limit exceeded' }.to_json
    end
  end

  get '/health' do
    { status: 'ok', service: 'api-gateway' }.to_json
  end

  get '/api/*' do
    start_time = Time.now

    path = "/api/#{params['splat'].first}"
    service_url = settings.router.route(path)

    if service_url.nil?
      settings.logger.log_request(request.request_method, path, 404, 0)
      halt 404, { error: 'Service not found' }.to_json
    end

    duration = ((Time.now - start_time) * 1000).round(2)
    settings.logger.log_request(request.request_method, path, 200, duration)

    { message: 'Request routed', service: service_url, path: path }.to_json
  end

  post '/api/*' do
    start_time = Time.now

    path = "/api/#{params['splat'].first}"
    service_url = settings.router.route(path)

    if service_url.nil?
      settings.logger.log_request(request.request_method, path, 404, 0)
      halt 404, { error: 'Service not found' }.to_json
    end

    duration = ((Time.now - start_time) * 1000).round(2)
    settings.logger.log_request(request.request_method, path, 200, duration)

    { message: 'Request routed', service: service_url, path: path }.to_json
  end

  run! if app_file == $0
end
