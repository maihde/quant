LICENSE="""
This module is released under the GNU Lesser General Public License,
the wording of which is available on the GNU website, http://www.gnu.org
"""

"""
YahooQuote - a set of classes for fetching stock quotes from
finance.yahoo.com

Created by David McNab ((david AT conscious DOT co DOT nz))

Originally this was a wrapper of the original
'pyq' utility by Rimon Barr:
    - http://www.cs.cornell.edu/barr/repository/pyq/index.html
But now, the back-end has been completely re-written.

The original version stored stock quotes in a MetaKit database
file.  Since metakit isn't available as a Ubuntu package, the
cache storage has been changed to sqlite3 to be as portable 
as possible.

Usage Examples::

 >>> import YahooQuote

 >>> market = YahooQuote.Market()

 >>> redhat = market['rht']
 >>> redhat
 <Ticker:rht>

 >>> redhat[20070601]
 <Quote:rht/20070601:m=-0.31 o=24.88 c=24.57 l=24.40 h=25.25 a=24.57 v=8579200>

 >>> redhat.now  # magic attribute via __getattr__
 <Quote:rht/20071506:m=-0.22 o=23.50 c=23.28 l=23.22 h=23.75 a=23.28 v=1185200>

 >>> ms = market['msft']
 >>> ms
 <Ticker:msft>  # note the 'dji/msft', meaning that MS is on DJI index

 >>> ms[20070604:20070609]  # get range of dates as slice - Jun4 - Jun8
 [<Quote:msft/20070604:m=+0.30 o=30.42 c=30.72 l=30.40 h=30.76 a=30.72 v=41434500>, 
 <Quote:msft/20070605:m=-0.04 o=30.62 c=30.58 l=30.33 h=30.63 a=30.58 v=44265000>, 
 <Quote:msft/20070606:m=-0.08 o=30.37 c=30.29 l=30.25 h=30.53 a=30.29 v=38217500>, 
 <Quote:msft/20070607:m=-0.40 o=30.02 c=29.62 l=29.59 h=30.29 a=29.62 v=71971400>]

 >>> lastThu = ms[20070614]  # fetch a single trading day

 >>> lastThu
 <Quote:msft/20070614:m=+0.17 o=30.35 c=30.52 l=30.30 h=30.71 a=30.52 v=59065700>

 >>> lastThu.__dict__      # see what is in a Quote object
 {'volume': 59065700, 'open': 30.350000000000001, 'high': 30.710000000000001,
  'adjclose': 30.52, 'low': 30.300000000000001, 'date': '20070614',
  'close': 30.52, 'ticker': <Ticker:dji/msft>}

 >>> ms[20070603]  # sunday, markets closed, build dummy quote from Friday
 <Quote:msft/20070603:m=0.00 o=30.59 c=30.59 l=30.59 h=30.59 a=30.59 v=0>

Read the API documentation for further features/methods
"""

import os, sys, re, traceback, getopt, time
#import strptime
import urllib
import weakref, gc
import csv
import logging
import Queue, thread, threading
import datetime
import sqlite3

Y2KCUTOFF=60
__version__ = "0.4"

CACHE='~/.quant/stocks.db'

MONTH2NUM = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

DAYSECS = 60 * 60 * 24

DEBUG = 0

ENABLE_INTERPOLATION = False

# base URLs for fetching quotes and history
baseUrlHistory = "http://ichart.finance.yahoo.com/table.csv"
baseUrlQuote = "http://download.finance.yahoo.com/d/quotes.csv"

fetchWindow = 90

# maximum number of threads for fetching histories
maxHistoryThreads = 10

# hardwired table listing the various stock indexes around the world.
# from time to time, this will need to be updated
indexes = {
    "DJA": {"name": "Dow Jones Composite", "country": "USA"},
    "DJI": {"name": "Dow Jones Industrial Average", "country": "USA"},
    "DJT": {"name": "Dow Jones Transportation Average", "country": "USA"},
    "DJU": {"name": "Dow Jones Utility Average", "country": "USA"},
    "NYA": {"name": "NYSE Composite", "country": "USA"},
    "NIN": {"name": "NYSE International 100", "country": "USA"},
    "NTM": {"name": "NYSE TMT", "country": "USA"},
    "NUS": {"name": "NYSE US 100", "country": "USA"},
    "NWL": {"name": "NYSE World Leaders", "country": "USA"},
    "IXBK":{"name": "NASDAQ Bank", "country": "USA"},
    "NBI": {"name": "NASDAQ Biotech", "country": "USA"},
    "IXIC":{"name": "NASDAQ Composite", "country": "USA"},
    "IXK": {"name": "NASDAQ Computer", "country": "USA"},
    "IXF": {"name": "NASDAQ Financial 100", "country": "USA"},
    "IXID":{"name": "NASDAQ Industrial", "country": "USA"},
    "IXIS":{"name": "NASDAQ Insurance", "country": "USA"},
    "IXQ": {"name": "NASDAQ NNM Composite", "country": "USA"},
    "IXFN":{"name": "NASDAQ Other Finance", "country": "USA"},
    "IXUT":{"name": "NASDAQ Telecommunications", "country": "USA"},
    "IXTR":{"name": "NASDAQ Transportation", "country": "USA"},
    "NDX": {"name": "NASDAQ-100 (DRM)", "country": "USA"},
    "OEX": {"name": "S&P 100 Index", "country": "USA"},
    "MID": {"name": "S&P 400 Midcap Index", "country": "USA"},
    "GSPC":{"name": "S&P 500 Index", "country": "USA"},
    "SPSUPX":{"name": "S&P Composite 1500 Index", "country": "USA"},
    "SML": {"name": "S&P Smallcap 600 Index", "country": "USA"},
    "XAX": {"name": "AMEX COMPOSITE INDEX", "country": "USA"},
    "IIX": {"name": "AMEX INTERACTIVE WEEK INTERNET", "country": "USA"},
    "NWX": {"name": "AMEX NETWORKING INDEX", "country": "USA"},
    "PSE": {"name": "ArcaEx Tech 100 Index", "country": "USA"},
    "DWC": {"name": "DJ WILSHIRE 5000", "country": "USA"},
    "XMI": {"name": "MAJOR MARKET INDEX", "country": "USA"},
    "SOXX": {"name": "PHLX SEMICONDUCTOR SECTOR INDEX", "country": "USA"},
    "DOT": {"name": "PHLX THESTREET.COM INTERNET SEC", "country": "USA"},
    "RUI": {"name": "RUSSELL 1000 INDEX", "country": "USA"},
    "RUT": {"name": "RUSSELL 2000 INDEX", "country": "USA"},
    "RUA": {"name": "RUSSELL 3000 INDEX", "country": "USA"},
    "MERV": {"name": "MerVal", "country": "?"},
    "BVSP": {"name": "Bovespa", "country": "?"},
    "GSPTSE": {"name": "S&P TSX Composite", "country": "?"},
    "MXX": {"name": "IPC", "country": "?"},
    "GSPC": {"name": "500 Index", "country": "?"},
    "AORD": {"name": "All Ordinaries", "country": "Australia"},
    "SSEC": {"name": "Shanghai Composite", "country": "China"},
    "HSI": {"name": "Hang Seng", "country": "Hong Kong"},
    "BSESN": {"name": "BSE", "country": "?"},
    "JKSE": {"name": "Jakarta Composite", "country": "Indonesia"},
    "KLSE": {"name": "KLSE Composite", "country": "?"},
    "N225": {"name": "Nikkei 225", "country": "Japan"},
    "NZ50": {"name": "NZSE 50", "country": "New Zealand"},
    "STI": {"name": "Straits Times", "country": "?"},
    "KS11": {"name": "Seoul Composite", "country": "?"},
    "TWII": {"name": "Taiwan Weighted", "country": "Taiwan"},
    "ATX": {"name": "ATX", "country": "?"},
    "BFX": {"name": "BEL-20", "country": "?"},
    "FCHI": {"name": "CAC 40", "country": "?"},
    "GDAXI": {"name": "DAX", "country": "?"},
    "AEX": {"name": "AEX General", "country": "?"},
    "OSEAX": {"name": "OSE All Share", "country": "?"},
    "MIBTEL": {"name": "MIBTel", "country": "?"},
    "IXX": {"name": "ISE National-100", "country": "?"},
    "SMSI": {"name": "Madrid General", "country": "Spain"},
    "OMXSPI": {"name": "Stockholm General", "country": "Sweden"},
    "SSMI": {"name": "Swiss Market", "country": "Swizerland"},
    "FTSE": {"name": "FTSE 100", "country": "UK"},
    "CCSI": {"name": "CMA", "country": "?"},
    "TA100": {"name": "TA-100", "country": "?"},
    }


class SymbolNotFound(Exception):
    pass


class Cache:
    """
    Class that provides the cache using sqllite.
    """
    HISTORY_COL_DEF=(
        "stock_id integer primary key autoincrement",
        "symbol text not null",
        "date date",
        "open float",
        "close float",
        "low float",
        "high float",
        "volume float",
        "adjclose float")

    def __init__(self):
        dbPath = os.path.expanduser(CACHE)
        dbDir = os.path.split(dbPath)[0]
        if not os.path.isdir(dbDir):
            os.mkdir(dbDir)

        self.db = sqlite3.connect(dbPath)

        cursor = self.db.cursor()
	cursor.execute("CREATE TABLE IF NOT EXISTS history (%s)" % (", ".join(Cache.HISTORY_COL_DEF)))
	cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ticker ON history (symbol, date ASC)")
	cursor.close()

    def symbols(self):
        """Return a list of symbols that have been cached."""
	cursor = self.db.cursor()
	symbols = cursor.execute("select distinct symbol from history").fetchall()
	cursor.close()
        return [x[0] for x in symbols]

    def get(self, symbol, wantDate, priorDate=None):
	cursor = self.db.cursor()
        if priorDate == None:
            hist = cursor.execute("SELECT * FROM HISTORY WHERE (date='%s' and symbol='%s')" % (wantDate, symbol)).fetchall()
        else:
            hist = cursor.execute("SELECT * FROM HISTORY WHERE (date>='%s' and date<='%s' and symbol='%s')" % (priorDate, wantDate, symbol)).fetchall()
        return [Quote.fromRow(x) for x in hist]

    def init(self, symbol, wantDate, priorDate):
        d = priorDate
        while d <= wantDate:
            cursor = self.db.cursor()
            cursor.execute("INSERT OR REPLACE INTO HISTORY VALUES (NULL, '%s', '%s', NULL, NULL, NULL, NULL, NULL, NULL)" % (symbol, d))
            cursor.close()
            d += 1
        self.db.commit()

    def put(self, quotes):
        for quote in quotes:
            cursor = self.db.cursor()
            cursor.execute("INSERT OR REPLACE INTO HISTORY VALUES (NULL, '%(symbol)s', '%(date)s', '%(open)s', %(close)f, %(low)f, %(high)f, %(volume)f, %(adjclose)f)" % quote.__dict__)
            cursor.close()
        self.db.commit()

    def purge(self, symbol):
	cursor = self.db.cursor()
	hist = cursor.execute("DELETE FROM HISTORY WHERE (symbol='%s')" % (symbol)).fetchall()
	cursor.close()
        self.db.commit()

    def __del__(self):
        try:
            self.db.commit()
        except:
            pass


class Market:
    """
    Main top-level class for YahooQuote.

    Holds/fetches info on a per-ticker basis

    Use this like a dict, where the keys are ticker symbols,
    and the values are Ticker objects (see class Ticker)
    """
    def __init__(self):
        """
        Creates a 'Market' object, which accesses quotes for
        various ticker symbols through Ticker object

        No args or keywords needed.
        """
        self.cache = Cache()

        self.indexes = {}
        self.tickersBySymbol = {}
        self.symbolIndex = {}

    def loadIndexes(self):
        """
        loads all index components.

        The first time this method is executed, it will download
        a list of component stocks for each index and store them in the
        database.

        Subsequent calls to this method, even in future sessions, will
        just load these component stock lists from the database
        """
        logging.debug("loading indexes and components")
        # load up all the indexes and their parts
        for symbol in indexes.keys():
            idx = Index(self, symbol, **indexes[symbol])
            self.indexes[symbol] = idx
            for stocksym in idx.components:
                self.symbolIndex[stocksym] = symbol
        logging.debug("  index components loaded")


    def __getitem__(self, symbol):
        """
        If 'symbol' is an index, returns an L{Index} object for that index symbol.

        If 'symbol' is an individual stock symbol, then returns a L{Ticker}
        object for that stock
        """
        su = symbol.upper()
        if su in self.indexes:
            return self.indexes[su]

        # we store weak refs to the tickers, to save memory when
        # the tickers go away
        ticker = None
        ref = self.tickersBySymbol.get(symbol, None)
        if ref:
            ticker = ref()

        if not ticker:
            ticker = Ticker(self, symbol)
            self.tickersBySymbol[symbol] = weakref.ref(ticker)

        return ticker


    def fetchHistory(self):
        """
        Fetches all history for all known stocks

        This can take an hour or more, even with a broadband connection, and
        will leave you with a cache file of over 100MB.

        If you're only interested in specific stocks or indexes, you might prefer
        to invoke L{Index.fetchHistory} or L{Ticker.FetchHistory}, respectively.
        """
        logging.info("fetching history for all stocks")
        if len(self.indexes.values()) == 0:
	    self.loadIndexes()

        try:
            for index in self.indexes.values():
                # fill the queue with callable methods
		logging.debug("fetching index %s", index)
                index.fetchHistory()
        except KeyboardInterrupt:
            logging.info("interrupted by user")

    def updateHistory(self):
        """
        Updates all known stocks' histories. Don't run this unless
        you have previously invoked L{Market.fetchHistory}
        """
        for symbol in self.cache.symbols():
	    logging.debug("updating symbol %s", symbol)
            ticker = self[symbol]
            ticker.updateHistory()


class Index:
    """
    encapsulates a stock index, eg 'dji' for dow jones
    """
    def __init__(self, market, symbol, **kw):
        """
        Creates a market index container. You shouldn't normally have to
        create these yourself.
        """
        symbol = symbol.lower()
        self.market = market
        self.symbol = symbol
        self.__dict__.update(kw)

        # fetch the components from yahoo
        self.components = []
	self.fetchFromYahoo()

    def __repr__(self):

        return "<Index:%s>" % self.symbol


    def load(self, row):
        """
        loads component names from database
        """
        for symbolRow in row.stocks:
            self.components.append(symbolRow.symbol)

    def fetchFromYahoo(self):
        """
        retrieves a list of component stocks for this index from the
        Yahoo Finance website
        """
        logging.debug("Refreshing list of component stocks for %s" % self.symbol)

        # create args
        parmsDict = {
            "s": "@^"+self.symbol.upper(),
            "f": "sl1d1t1c1ohgv",
            "e": ".csv",
            "h": 0,
            }
        parms = "&".join([("%s=%s" % (k,v)) for k,v in parmsDict.items()])

        # construct full URL
        url = "http://download.finance.yahoo.com/d/quotes.csv?%s" % parms

        # get the CSV for this index
        f = urllib.urlopen(url)
        lines = f.readlines()
        csvReader = csv.reader(lines)

        # extract the component symbols
        componentSymbols = [item[0].lower() for item in csvReader if item]

        # save to database
        for symbol in componentSymbols:
            self.components.append(symbol)

    def fetchHistory(self):
        """
        Invokes L{Ticker.fetchHistory} on all component stocks of this index
        """
        logging.debug("index %s" % self.symbol)

        for sym in self.components:

            ticker = self.market[sym]
            ticker.fetchHistory()

    def __getitem__(self, symbol):
        """
        retrieves a component ticker
        """
        return self.market[self.components[symbol]]



class Ticker:
    """
    Represents the prices of a single ticker symbol.

    Works as a smart sequence, keyed by yyyymmdd numbers

    The magic attribute 'now' fetches current prices
    """
    baseUrlQuote = baseUrlQuote
    baseUrlHistory = baseUrlHistory

    def __init__(self, market, symbol, index=None):
        """
        Create a Ticker class, which gets/caches/retrieves quotes
        for a single ticker symbol

        Treat objects of this class like an array, where you can get
        a single item (date) to return a Quote object for the symbol 
        and date, or get a slice, to return a list of Quote objects
        for the date range.

        Note - you shouldn't instantiate this class directly, but instead
        get an instance by indexing a L{Market} object - see
        L{Market.__getitem__}
        """
        self.market = market

        self.symbol = symbol.lower()
        index = index or self.market.symbolIndex.get(symbol, None)
        if isinstance(index, str):
            index = self.market[index]
        self.index = index

        self.dates = {}

        self.firstKey = "first"
        self.lastKey = "last"

    def getQuote(self):
        """
        Returns a Quote object for this stock
        """
        # construct the query URL
        #?s=MSFT&f=sl1d1t1c1ohgv&e=.csv
        baseUrl = self.baseUrlQuote
        parms = [
            "s=%s" % self.symbol,
            "f=sl1d1t1c1ohgv",
            "e=.csv",
            ]
        url = baseUrl + "?" + "&".join(parms)

        # get the raw csv lines from Yahoo
        lines = urllib.urlopen(url).readlines()

        # and get the quote from it
        return Quote.fromYahooQuote(self, lines[0])

    def __getitem__(self, date):
        """
        Retrieves/creates a Quote object for this ticker's prices
        for a particular date
        """
        logging.debug("date=%s", date)

        logging.debug("%s(1): refs=%s" % (self.symbol, self.refs))

        now = QuoteDate.now()

        if isinstance(date, slice):
            # give back a slice
            priorDate = QuoteDate(date.start)
            wantDate = QuoteDate(date.stop)
        else:
            wantDate = date
            priorDate = None

        if not isinstance(wantDate, QuoteDate):
            wantDate = QuoteDate(wantDate)
        if priorDate != None and not isinstance(priorDate, QuoteDate):
            priorDate = QuoteDate(priorDate)

        # attempted prescience?
        if wantDate > now or priorDate > now:
            raise IndexError("Prescience disabled by order of Homeland Security")

        # no, seek it from db or yahoo
        quotes = self.market.cache.get(self.symbol, wantDate, priorDate)
        if priorDate == None:
            expectedQuotes = 1
        else:
            expectedQuotes = (wantDate - priorDate) + 1
        if len(quotes) != expectedQuotes:
            self._fetch(wantDate, priorDate)
            quotes = self.market.cache.get(self.symbol, wantDate, priorDate)
       
        if isinstance(date, slice):
            return quotes
        else:
            return quotes[0]

    def __repr__(self):
        if self.index:
            idx = "%s/" % self.index.symbol
        else:
            idx = ""
        return "<Ticker:%s%s>" % (idx, self.symbol)

    def __getattr__(self, attr):
        """
        Intercept attribute 'now' to mean a fetch of present prices
        """
        if attr in ['now', 'today']:
            return self.getQuote()

        if attr == 'refs':
            return len(gc.get_referrers(self))

        raise AttributeError(attr)

    def _fetch(self, wantDate, priorDate=None, checkDuplicates=True):
        """
        fetches a range of quotes from site, hopefully
        including given date, and stores these in the database

        argument 'date' MUST be a QuoteDate object
        """
        if not isinstance(wantDate, QuoteDate):
            raise Exception("Invalid date %s: not a QuoteDate" % wantDate)

        # go some days before and after
        if priorDate == None:
            priorDate = wantDate - fetchWindow + 1
        year1, month1, day1 = priorDate.toYmd()
        year2, month2, day2 = (wantDate + 1).toYmd()

        self.market.cache.init(self.symbol, wantDate, priorDate)
        logging.info("fetching %s for %s-%s-%s to %s-%s-%s" % (
                    self.symbol,
                    year1, month1, day1,
                    year2, month2, day2))

        baseUrl = self.baseUrlHistory
        parms = [
            "s=%s" % self.symbol.upper(),
            "a=%d" % (month1-1),
            "b=%d" % day1,
            "c=%d" % year1,
            "d=%d" % (month2-1),
            "e=%d" % day2,
            "f=%d" % year2,
            "g=d",
            "ignore=.csv",
            ]

        url = baseUrl + "?" + "&".join(parms)
        logging.debug("  fetching URL %s", url)
        #print "url=%s" % url

        # get the raw csv lines from Yahoo
        resp = urllib.urlopen(url)
        if resp.getcode() == 404:
            logging.info("%s: No history for %04d-%02d-%02d to %04d-%02d-%02d" % (
                        self.symbol,
                        year1, month1, day1,
                        year2, month2, day2))
            return
        lines = resp.readlines()

        logging.debug("   fetched %s", lines)

        if lines[0].startswith("Date"):
            lines = lines[1:]

        quotes = []
        try:
            quotes = [Quote.fromYahooHistory(self.symbol, line) for line in lines]
        except:
            logging.exception("Failed to process yahoo data")

        if len(quotes) == 0:
            logging.info("%s: No history for %04d-%02d-%02d to %04d-%02d-%02d" % (
                        self.symbol,
                        year1, month1, day1,
                        year2, month2, day2))
        else:        
            # sort quotes into ascending order and fill in any missing dates
            quotes.sort(lambda q1, q2: cmp(q1.date, q2.date))
            self.market.cache.put(quotes)

    def fetchHistory(self, start=None, end=None):
        """
        fetches this stock's entire history - you should only ever
        do this once, and thereafter, invoke
        L{Ticker.updateHistory} to keep the history up to date
        """
        if start == None:
            startDay = QuoteDate.fromYmd(1950, 1, 1)
        else:
            startDay = QuoteDate(end)

        if end == None:
            endDay = QuoteDate.now()
        else:
            endDay = QuoteDate(start)

	cursor = self.market.cache.purge(self.symbol)

        try:
            # now get the whole history, lock stock and barrel
            self._fetch(endDay, startDay, False)
        except KeyboardInterrupt:
            raise
        except:
            logging.exception("%s: failed to fetch" % self.symbol)

    def updateHistory(self, start=None, end=None):
        """
        Updates this stock's history. You should not invoke this
        method unless you have invoked L{Ticker.fetchHistory} at
        some time in the past.
        """
        if end == None:
            end = QuoteDate.now()
        if start == None:
            cursor = self.market.db
            lastdate = cursor.execute("select MAX(date) from history where (symbol='%s')" % self.symbol).fetchone()[0]
	    start = QuoteDate(lastdate) + 1

        if not isinstance(start, QuoteDate):
            start = QuoteDate(start)
        if not isinstance(end, QuoteDate):
            end = QuoteDate(end)

        if end <= start:
            return

        quotes = self.market.cache.get(self.symbol, end, start)
        if (len(quotes) - 1) != (end - start):
            self._fetch(end, start)

class Quote:
    """
    dumb object which wraps quote data
    """
    def __init__(self, symbol, **kw):
        self.symbol = symbol
        self.date=None
        self.open=None
        self.close=None
        self.low=None
        self.high=None
        self.volume=None
        self.adjclose=None
        self.__dict__.update(kw)

    # Normalization concept from http://luminouslogic.com/how-to-normalize-historical-data-for-splits-dividends-etc.htm
    def get_adjopen(self):
        if self.adjclose:
            return (self.adjclose / self.close) * self.open
        else:
            return None
    adjopen = property(fget=get_adjopen)

    def get_adjlow(self):
        if self.adjclose:
            return (self.adjclose / self.close) * self.low
        else:
            return None
    adjlow = property(fget=get_adjlow)

    def get_adjhigh(self):
        if self.adjclose:
            return (self.adjclose / self.close) * self.high
        else:
            return None
    adjhigh = property(fget=get_adjhigh)

    def __repr__(self):

    #        date = "%04d%02d%02d" % (year, month, day)
    #        quoteDict['open'] = float(open)
    #        quoteDict['high'] = float(high)
    #        quoteDict['low'] = float(low)
    #        quoteDict['close'] = float(close)
    #        quoteDict['volume'] = float(vol)
    #        quoteDict['adjclose'] = float(adjclose)


        if None in (self.open, self.close, self.low, self.high, self.adjclose, self.volume):
            return "<Quote:%s/%s>" % (self.symbol, self.date)
        else: 
            if self.close > self.open:
                m = "+%.02f" % (self.close - self.open)
            elif self.close < self.open:
                m = "%.02f" % (self.close - self.open)
            else:
                m = "0.00"
            return "<Quote:%s/%s:m=%s o=%.2f c=%.2f l=%.2f h=%.2f a=%.2f v=%d>" \
                    % (self.symbol,
                       self.date,
                       m,
                       self.open, self.close,
                       self.low, self.high,
                       self.adjclose,
                       self.volume)

    def fromYahooHistory(symbol, line):
        """
        Static method - reads a raw line from yahoo history
        and returns a Quote object
        """
        #logging.info("fromYahooHistory: line=%s" % repr(line))

        items = csv.reader([line]).next()

        logging.debug("items=%s" % str(items))

        ydate, open, high, low, close, vol, adjclose = items

        # determine date of this next result
        quote = Quote(symbol, 
                      date=QuoteDate.fromYahoo(ydate),
                      open=float(open),
                      close=float(close),
                      low=float(low),
                      high=float(high),
                      volume=int(vol),
                      adjclose=float(adjclose))
        return quote

    fromYahooHistory = staticmethod(fromYahooHistory)

    def fromYahooQuote(symbol, line):
        """
        Static method - given a ticker object and a raw quote line from Yahoo for
        that ticker, build and return a Quote object with that data
        """
        # examples:
        # sym    last   d/m/y     time        change  open   high   low    volume
        # MSFT,  30.49,	6/15/2007,4:00:00 PM, -0.03,  30.88, 30.88, 30.43, 100941384
        # TEL.NZ,4.620, 6/15/2007,12:58am,    0.000,  4.640, 4.640, 4.590, 3692073

        items = csv.reader([line]).next()
        sym, last, date, time, change, open, high, low, volume = items

        # massage/convert the fields
        sym = sym.lower()
        last = float(last)

        day, month, year = [int(f) for f in date.split("/")]

        date = QuoteDate.fromYmd(year, month, day)
        if change.startswith("-"):
            change = -float(change[1:])
        elif change.startswith("+"):
            change = float(change[1:])
        else:
            change = float(change)
        open = float(open)
        close = last
        high = float(high)
        low = float(low)
        volume = float(volume)
        adjclose = last

        # got all the bits, now can wrap a Quote
        return Quote(sym,
                     date=date,
                     open=open,
                     close=last,
                     high=high,
                     low=low,
                     volume=volume,
                     adjclose=adjclose)

    fromYahooQuote = staticmethod(fromYahooQuote)

    def fromRow(row):
        """
        Static method - Constructs a L{Quote} object from a given sqlite row
        """
        return Quote(symbol=row[1],
                    date=row[2],
                    open=row[3],
                    close=row[4],
                    low=row[5],
                    high=row[6],
                    volume=row[7],
                    adjclose=row[8])

    fromRow = staticmethod(fromRow)


class QuoteDate(int):
    """
    Simple int subclass that represents yyyymmdd quote dates
    """
    def __new__(cls, val):
        """
        Create a QuoteDate object. Argument can be an int or string,
        as long as it is in the form YYYYMMDD
        """
        if isinstance(val, datetime.datetime):
            val = (val.year * 10000) + (val.month * 100) + val.day
        inst = super(QuoteDate, cls).__new__(cls, val)
        inst.year, inst.month, inst.day = inst.toYmd()
        return inst

    def __add__(self, n):
        """
        Adds n days to this QuoteDate, and returns a new QuoteDate object
        """
        return QuoteDate.fromUnix(self.toUnix() + n * DAYSECS)

    def __sub__(self, n):
        """
        Subtracts n days from this QuoteDate, and returns a new QuoteDate object
        """
        if isinstance(n, QuoteDate):
            return int((self.toUnix() - n.toUnix()) / DAYSECS)
        else:
            return QuoteDate.fromUnix(self.toUnix() - n * DAYSECS)

    def toUnix(self):
        """
        Converts this QuoteDate object to a unix 'seconds since epoch'
        time
        """
        return time.mktime(self.toYmd() + (0,0,0,0,0,0))

    def fromUnix(udate):
        """
        Static method - converts a unix 'seconds since epoch'
        date into a QuoteDate string
        """
        return QuoteDate(time.strftime("%Y%m%d", time.localtime(float(udate))))

    fromUnix = staticmethod(fromUnix)

    def toDateTime(self):
        return datetime.date.fromtimestamp(self.toUnix())

    def now():
        """
        Static method - returns a QuoteDate object for today
        """
        return QuoteDate.fromUnix(time.time())

    now = staticmethod(now)

    def toYmd(self):
        """
        returns tuple (year, month, day)
        """
        s = "%08d" % self
        return int(s[0:4]), int(s[4:6]), int(s[6:8])

    def fromYmd(year, month, day):
        """
        Static method - instantiates a QuoteDate
        set to given year, month, day
        """
        return QuoteDate("%04d%02d%02d" % (int(year), int(month), int(day)))

    fromYmd = staticmethod(fromYmd)

    def fromYahoo(ydate):
        """
        Static method - converts a 'yyyy-mmm-dd'
        yahoo date into a QuoteDate object
        """
        dateFields = ydate.split("-")
        year = int(dateFields[0])
        try:
            monthStr = MONTH2NUM[dateFields[1]]
        except:
            monthStr = dateFields[1]
        month = int(monthStr)
        day = int(dateFields[2])
        return QuoteDate.fromYmd(year, month, day)

    fromYahoo = staticmethod(fromYahoo)
