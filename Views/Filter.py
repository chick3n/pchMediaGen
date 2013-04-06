import string

class Filter(object):
    episode = None
    show = None
    movie = None
    FILTER_NOTSEEN = 0
    FILTER_LETTER = 1
    FILTER_LETTER_EPISODE = 2

    # RAW FILTERS
    FILTER_SHOWID = 100
    FILTER_SEASON = 101

    def __init__(self, media, columnNames, filters = None):
        super(Filter, self).__init__()
        self.media = media
        self.filters = filters
        if media == "tv":
            self.episode = columnNames["episode"] if not None else None
            self.show = columnNames["show"] if not None else None
        elif media == "movie":
            self.movie = columnNames["movie"] if not None else None

    @staticmethod
    def ParseFilter(urlFilter):
        filters = urlFilter.split(",")
        filterList = ()

        for filter in filters:
            seq = filter.split(":")
            if seq is None:
                break

            if seq[0] == "s" and len(seq) > 1: # search parameter
                if seq[1] == 'Other':
                    filterList += (Filter.FILTER_LETTER, '#',)
                else: filterList += (Filter.FILTER_LETTER, seq[1].upper(),)

        return filterList if len(filterList) > 0 else None

    @staticmethod
    def ModifyFilter(FilterType, filters, newHeader, newValue):
        newTuple = ()
        for x in range(0, len(filters)):
            if filters[x][0] == FilterType:
                if newHeader is None:
                    newHeader = filters[x][0]
                if newValue is None:
                    newValue = filters[x][1]
                newTuple += (newHeader, newValue),
            else:
                newTuple += filters[x],

        return newTuple

    def genFilter(self, filters = None):
        if self.media == "tv":
            return self.genFilterTv(filters) if filters is not None else self.genFilterTv(self.filters)
        elif self.media == "movie":
            return self.genFilterMovie(filters) if filters is not None else self.genFilterMovie(self.filters)

        return ""

    def genFilterMovie(self, f):
        filterQuery = []
        usedMovie = False

        for filter in f:
            if filter[0] == self.FILTER_NOTSEEN:
                filterQuery.append(" %s.watched is null " % self.movie)
                usedMovie = True
            elif filter[0] == self.FILTER_LETTER:
                if filter[1] == '#':
                    filterQuery.append(" upper(substr(%s.parent_dir,1,1)) not in (%s) " % (self.movie, (",").join("'" + item + "'" for item in string.ascii_uppercase)))
                else: filterQuery.append(" %s.parent_dir like '%s%%' " % (self.movie, filter[1]))
                usedMovie = True

        if usedMovie and self.movie is None:
            return ""

        if filterQuery.__len__() > 0:
            return " WHERE " + " AND ".join(filterQuery)

        return ""

    def genFilterTv(self, f):
        filterQuery = []
        usedEpisode = False
        usedShow = False

        for filter in f:
            if filter[0] == self.FILTER_NOTSEEN:
                filterQuery.append(" %s.watched is null " % self.episode)
                usedEpisode = True
            elif filter[0] == self.FILTER_LETTER:
                if filter[1] == '#':
                    filterQuery.append(" upper(substr(%s.title,1,1)) not in (%s) " % (self.show, (",").join("'" + item + "'" for item in string.ascii_uppercase)))
                else: filterQuery.append(" %s.title like '%s%%' " % (self.show, filter[1]))
                usedShow = True
            elif filter[0] == self.FILTER_LETTER_EPISODE:
                if filter[1] == '#':
                    filterQuery.append(" (upper(substr(%(col)s.title,1,1)) not in (%(filter)s) or (%(col)s.title is null AND upper(substr(%(col)s.file_name,1,1)) not in (%(filter)s))) "
                                       % {"col":self.episode, "filter":(",").join("'" + item + "'" for item in string.ascii_uppercase)})
                else: filterQuery.append(" (%(col)s.title like '%(filter)s%%' or (%(col)s.title is null AND %(col)s.file_name like '%(filter)s%%')) "
                                   % {"col":self.episode, "filter":filter[1]})
                usedEpisode = True

            #raw filters
            elif filter[0] == self.FILTER_SHOWID:
                filterQuery.append(" %s.show = %s " % (self.episode, filter[1]))
                usedEpisode = True
            elif filter[0] == self.FILTER_SEASON:
                filterQuery.append(" %s.season = %s " % (self.episode, filter[1]))
                usedEpisode = True

        if usedEpisode and self.episode is None:
            return ""
        if usedShow and self.show is None:
            return ""

        if filterQuery.__len__() > 0:
            return " WHERE " + " AND ".join(filterQuery)

        return ""

    @staticmethod
    def getFilterValue(filterType, filters):
        for x in range(0, len(filters)):
            if filters[x][0] == filterType:
                return filters[x][1]

        return None