class Router
  SERVICES = {
    auth: 'http://localhost:8080',
    analytics: 'http://localhost:8000',
    products: 'http://localhost:9000'
  }.freeze

  def initialize
    @route_cache = {}
  end

  def route(path)
    return @route_cache[path] if @route_cache.key?(path)

    service = determine_service(path)
    @route_cache[path] = service
    service
  end

  def determine_service(path)
    case path
    when /^\/api\/auth/
      SERVICES[:auth]
    when /^\/api\/analytics/
      SERVICES[:analytics]
    when /^\/api\/products/
      SERVICES[:products]
    else
      nil
    end
  end

  def build_url(service_url, path)
    return nil unless service_url

    "#{service_url}#{path}"
  end

  def validate_path(path)
    return false if path.nil? || path.empty?
    return false unless path.start_with?('/api/')

    true
  end

  def clear_cache
    @route_cache.clear
  end
end
