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

  def is_activity_endpoint?(path)
    return false if path.nil? || path.empty?

    activity_patterns = [
      /\/api\/analytics\/activity/,
      /\/api\/auth\/activity/,
      /\/api\/users\/.*\/activity/
    ]

    activity_patterns.any? { |pattern| path.match?(pattern) }
  end

  def extract_user_id(path)
    return nil if path.nil? || path.empty?

    match = path.match(/\/users\/([a-zA-Z0-9-]+)/)
    match ? match[1] : nil
  end

  def get_activity_service(path)
    return nil unless is_activity_endpoint?(path)

    if path.include?('/auth/')
      SERVICES[:auth]
    elsif path.include?('/analytics/')
      SERVICES[:analytics]
    else
      SERVICES[:analytics]
    end
  end

  def route_with_priority(path, is_critical = false)
    service = route(path)
    return nil unless service

    {
      service: service,
      path: path,
      priority: is_critical ? 'high' : 'normal',
      timestamp: Time.now
    }
  end
end
